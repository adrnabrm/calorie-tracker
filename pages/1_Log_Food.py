from datetime import date

import streamlit as st
from models.schemas import Food, LoggedEntry
from services.calculations import format_weight, scale_macros, to_grams
from services.db import delete_food, get_all_foods, insert_food, insert_logged_entry

st.set_page_config(page_title="Log Food", layout="centered")
st.title("Log Food")


def log_today(food: dict, eaten_grams: float, unit: str) -> None:
    macros = scale_macros(food, eaten_grams)
    insert_logged_entry(
        LoggedEntry(
            date=date.today().isoformat(),
            weight_grams=eaten_grams,
            calories=macros["calories"],
            protein=macros["protein"],
            carbs=macros["carbs"],
            fats=macros["fats"],
            food_id=food["id"],
            weight_unit=unit,
        )
    )


@st.dialog("Are you sure?")
def confirm_delete_food(food_id: str, name: str) -> None:
    st.write(f"Delete **{name}** from the library?")
    with st.container(horizontal=True):
        if st.button("Cancel"):
            st.rerun()
        if st.button("Delete", type="primary"):
            delete_food(food_id)
            load_foods.clear()
            st.rerun()


@st.cache_data(ttl=60)
def load_foods() -> list[dict]:
    return get_all_foods()


st.subheader("From library")
query = st.text_input("Search")
foods = load_foods()
if query:
    q = query.lower()
    foods = [f for f in foods if q in f["name"].lower()]
if not foods:
    st.info("No matching foods." if query else "No foods yet. Add one below.")
else:
    labels = {
        f["id"]: (
            f"{f['name']} ({format_weight(float(f['serving_grams']), f.get('serving_unit') or 'g')} serving)"
        )
        for f in foods
    }
    food_id = st.selectbox("Food", list(labels.keys()), format_func=lambda i: labels[i])
    food = next(f for f in foods if f["id"] == food_id)
    serving_unit = food.get("serving_unit") or "g"
    lib_eaten = st.number_input(
        "Amount eaten", min_value=0.1, value=1.0, step=1.0, key="lib_eaten"
    )
    lib_unit = st.segmented_control(
        "Unit", ["g", "oz"], default=serving_unit, key=f"lib_unit_{food_id}"
    )
    with st.container(horizontal=True):
        log_clicked = st.button("Log")
        del_clicked = st.button("Delete from library")
    if log_clicked:
        unit = lib_unit or serving_unit
        log_today(food, to_grams(lib_eaten, unit), unit)
        st.success("Logged.")
    if del_clicked:
        confirm_delete_food(food_id, food["name"])

st.subheader("New food")
with st.form("new_food"):
    name = st.text_input("Name")
    serving_size = st.number_input(
        "Serving size", min_value=0.1, value=1.0, step=1.0
    )
    serving_unit = st.segmented_control(
        "Serving unit", ["g", "oz"], default="g", key="new_serving_unit"
    )
    calories = st.number_input("Calories (per serving)", min_value=0.0, step=1.0)
    protein = st.number_input("Protein (g, per serving)", min_value=0.0, step=0.1)
    carbs = st.number_input("Carbs (g, per serving)", min_value=0.0, step=0.1)
    fats = st.number_input("Fats (g, per serving)", min_value=0.0, step=0.1)
    new_eaten = st.number_input(
        "Amount eaten", min_value=0.1, value=1.0, step=1.0, key="new_eaten"
    )
    new_unit = st.segmented_control(
        "Eaten unit", ["g", "oz"], default="g", key="new_eaten_unit"
    )
    submitted = st.form_submit_button("Save and log")

if submitted:
    unit = serving_unit or "g"
    eaten_unit = new_unit or unit
    serving_grams = to_grams(serving_size, unit)
    row = insert_food(
        Food(
            name=name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats,
            serving_grams=serving_grams,
            serving_unit=unit,
            source="manual",
        )
    )
    log_today(row, to_grams(new_eaten, eaten_unit), eaten_unit)
    load_foods.clear()
    st.success("Saved and logged.")
