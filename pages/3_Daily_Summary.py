from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from services.calculations import format_weight, macros_from_entries
from services.db import delete_logged_entry, get_entries_for_date, update_logged_entry

st.set_page_config(page_title="Daily Summary", layout="centered")
st.title("Daily Summary")


_OZ = 28.3495


@st.dialog("Are you sure?")
def confirm_delete_log(entry_id: str, name: str, day: str) -> None:
    st.write(f"Delete **{name}** from the **{day}** log?")
    with st.container(horizontal=True):
        if st.button("Cancel", key="log_del_cancel"):
            st.rerun()
        if st.button("Delete", type="primary", key="log_del_ok"):
            delete_logged_entry(entry_id)
            st.rerun()


@st.dialog("Edit entry")
def edit_log_dialog(entry: dict) -> None:
    food = entry.get("foods") or {}
    if isinstance(food, list):
        food = food[0] if food else {}
    meal = entry.get("meals") or {}
    if isinstance(meal, list):
        meal = meal[0] if meal else {}
    name = food.get("name") or meal.get("name") or "Unknown"
    unit = entry.get("weight_unit") or "g"
    og = float(entry["weight_grams"])
    serving_grams = float(food["serving_grams"]) if food.get("serving_grams") else None

    if unit == "serving" and serving_grams:
        display_val = og / serving_grams
        unit_label = "servings"
    elif unit == "oz":
        display_val = og / _OZ
        unit_label = "oz"
    else:
        display_val = og
        unit_label = "g"

    st.write(f"**{name}**")
    new_amount = st.number_input(
        f"Amount ({unit_label})",
        min_value=0.01,
        value=round(display_val, 3),
        step=0.5 if unit == "serving" else 1.0,
    )
    if st.button("Save", type="primary"):
        if unit == "serving" and serving_grams:
            new_grams = new_amount * serving_grams
        elif unit == "oz":
            new_grams = new_amount * _OZ
        else:
            new_grams = new_amount
        factor = new_grams / og if og > 0 else 1.0
        update_logged_entry(
            entry["id"],
            new_grams,
            float(entry["calories"]) * factor,
            float(entry["protein"]) * factor,
            float(entry["carbs"]) * factor,
            float(entry["fats"]) * factor,
        )
        st.rerun()

_today = datetime.now(ZoneInfo(st.context.timezone or "UTC")).date()
selected = st.date_input("Date", value=_today, max_value=_today)
day = selected.isoformat()

entries = get_entries_for_date(day)
stats = macros_from_entries(entries, day)

if not stats["targets"]:
    st.info("Set your targets on the Goals & Settings page first.")
else:
    labels = {
        "calories": "Calories",
        "protein": "Protein (g)",
        "carbs": "Carbs (g)",
        "fats": "Fats (g)",
    }
    for key, label in labels.items():
        eaten = stats["eaten"][key]
        target = stats["targets"][key]
        remaining = stats["remaining"][key]
        pct = min(stats["pct"][key] / 100.0, 1.0)
        st.write(f"**{label}** — {eaten:.0f} / {target:.0f} ({remaining:.0f} left)")
        st.progress(pct)

st.subheader("Logged")
if not entries:
    st.info("Nothing logged on this day.")
else:
    to_delete = None
    to_edit = None
    for entry in entries:
        food = entry.get("foods") or {}
        if isinstance(food, list):
            food = food[0] if food else {}
        meal = entry.get("meals") or {}
        if isinstance(meal, list):
            meal = meal[0] if meal else {}
        name = food.get("name") or meal.get("name") or "Unknown"
        if food.get("source") == "estimated" and food.get("name"):
            name = f"{name} (estimated)"
        food_serving_grams = float(food["serving_grams"]) if food.get("serving_grams") else None
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(
                f"**{name}** — "
                f"{format_weight(float(entry['weight_grams']), entry.get('weight_unit') or 'g', food_serving_grams)}, "
                f"{float(entry['calories']):.0f} cal · "
                f"{float(entry['protein']):.0f}p / {float(entry['carbs']):.0f}c / {float(entry['fats']):.0f}f"
            )
            if st.button("Edit", key=f"edit_{entry['id']}"):
                to_edit = entry
            if st.button("Delete", key=f"del_{entry['id']}"):
                to_delete = (entry["id"], name)
    if to_edit:
        edit_log_dialog(to_edit)
    if to_delete:
        confirm_delete_log(*to_delete, day)
