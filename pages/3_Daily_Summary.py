from datetime import date

import streamlit as st
from services.calculations import macros_for_date

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
