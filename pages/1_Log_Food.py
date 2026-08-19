from datetime import date
from typing import Literal

import streamlit as st
from models.schemas import Food, LoggedEntry
from services.calculations import format_weight, scale_macros, to_grams
from services.db import delete_food, get_all_foods, insert_food, insert_logged_entry
from services.gemini import GeminiError
from services.vision import estimate

_KEYS = ("calories", "protein", "carbs", "fats")
_SIZES: tuple[Literal["Small", "Typical", "Large"], ...] = ("Small", "Typical", "Large")

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


def _editor_rows(edited) -> list[dict]:
    records = edited.to_dict("records") if hasattr(edited, "to_dict") else list(edited)
    return [r for r in records if float(r.get("grams") or 0) > 0]


st.session_state.setdefault("vision_estimate", None)
st.session_state.setdefault("vision_id", 0)
st.session_state.setdefault("vision_error", None)

st.subheader("From photo")
camera = st.camera_input("Food photo")
upload = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png", "webp"])
image = camera or upload
photo_weight = st.number_input("Weight", min_value=0.0, value=0.0, step=1.0, key="vision_weight")
photo_unit = st.segmented_control("Unit", ["g", "oz"], default="g", key="vision_unit")
size = None
if photo_weight <= 0:
    size = st.segmented_control("Portion size", list(_SIZES), key="vision_size")
notes = st.text_input("Notes", placeholder="extra noodles, ate half", key="vision_notes")
if st.button("Estimate", key="vision_estimate_btn"):
    if not image:
        st.warning("Take or upload a photo first.")
    elif photo_weight <= 0 and not size:
        st.warning("Enter a weight or pick a portion size.")
    else:
        grams = to_grams(photo_weight, photo_unit or "g") if photo_weight > 0 else None
        size_key = None
        if photo_weight <= 0 and size:
            size_key = {"Small": "small", "Typical": "typical", "Large": "large"}[size]
        with st.spinner("Estimating"):
            try:
                st.session_state.vision_estimate = estimate(
                    image.getvalue(),
                    image.type or "image/jpeg",
                    grams=grams,
                    size=size_key,
                    notes=notes or "",
                )
                st.session_state.vision_id += 1
                st.session_state.vision_error = None
            except GeminiError as e:
                st.session_state.vision_estimate = None
                st.session_state.vision_error = str(e)

if st.session_state.vision_error:
    st.error(st.session_state.vision_error)
elif st.session_state.vision_estimate is not None:
    vision = st.session_state.vision_estimate
    if not vision.is_food:
        st.error("No food in this photo.")
    else:
        vid = st.session_state.vision_id
        if vision.reasoning:
            st.caption(vision.reasoning)
        name = st.text_input("Name", value=vision.name, key=f"vision_name_{vid}")
        edited = st.data_editor(
            [c.model_dump() for c in vision.components],
            column_config={
                "name": st.column_config.TextColumn("Name", required=True),
                "grams": st.column_config.NumberColumn("g", min_value=0.1, step=1.0),
                "calories": st.column_config.NumberColumn("Calories", min_value=0.0, step=1.0),
                "protein": st.column_config.NumberColumn("Protein", min_value=0.0, step=0.1),
                "carbs": st.column_config.NumberColumn("Carbs", min_value=0.0, step=0.1),
                "fats": st.column_config.NumberColumn("Fats", min_value=0.0, step=0.1),
            },
            num_rows="dynamic",
            hide_index=True,
            key=f"vision_rows_{vid}",
        )
        rows = _editor_rows(edited)
        total_g = sum(float(r["grams"]) for r in rows)
        totals = {k: sum(float(r.get(k) or 0) for r in rows) for k in _KEYS}
        st.write(
            f"**{total_g:g} g** — {totals['calories']:.0f} cal, "
            f"{totals['protein']:.0f}p / {totals['carbs']:.0f}c / {totals['fats']:.0f}f"
        )
        with st.container(horizontal=True):
            log_photo = st.button("Log", key="vision_log")
            discard_photo = st.button("Discard", key="vision_discard")
        if discard_photo:
            st.session_state.vision_estimate = None
            st.session_state.vision_error = None
            st.session_state.vision_id += 1
            st.rerun()
        if log_photo:
            if not name.strip():
                st.warning("Enter a name.")
            elif total_g <= 0:
                st.warning("Add at least one row with grams.")
            else:
                factor = 100.0 / total_g
                row = insert_food(
                    Food(
                        name=name.strip(),
                        calories=totals["calories"] * factor,
                        protein=totals["protein"] * factor,
                        carbs=totals["carbs"] * factor,
                        fats=totals["fats"] * factor,
                        serving_grams=100.0,
                        serving_unit="g",
                        source="estimated",
                    )
                )
                log_today(row, total_g, "g")
                load_foods.clear()
                st.session_state.vision_estimate = None
                st.session_state.vision_error = None
                st.session_state.vision_id += 1
                st.success("Logged.")

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
            f"{f['name']}"
            f"{' (estimated)' if f.get('source') == 'estimated' else ''}"
            f" ({format_weight(float(f['serving_grams']), f.get('serving_unit') or 'g')} serving)"
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
    if not name.strip():
        st.warning("Enter a name.")
    else:
        unit = serving_unit or "g"
        eaten_unit = new_unit or unit
        serving_grams = to_grams(serving_size, unit)
        row = insert_food(
            Food(
                name=name.strip(),
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
