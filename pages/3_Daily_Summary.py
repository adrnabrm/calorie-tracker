from datetime import date

import streamlit as st
from services.calculations import format_weight, macros_for_date
from services.db import get_entries_for_date, get_food_by_id

st.set_page_config(page_title="Daily Summary", layout="centered")
st.title("Daily Summary")

today = date.today().isoformat()
st.caption(today)

stats = macros_for_date(today)

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
entries = get_entries_for_date(today)
if not entries:
    st.info("Nothing logged today.")
else:
    for entry in entries:
        food = get_food_by_id(entry["food_id"]) if entry.get("food_id") else None
        name = (food or {}).get("name") or "Unknown"
        st.write(
            f"**{name}** — {format_weight(float(entry['weight_grams']), entry.get('weight_unit') or 'g')}, "
            f"{float(entry['calories']):.0f} cal"
        )
