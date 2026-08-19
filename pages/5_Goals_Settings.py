import streamlit as st
from models.schemas import Goals
from services.db import get_goals_for_date, upsert_goals

st.set_page_config(page_title="Goals & Settings", layout="centered")
st.title("Goals & Settings")

selected = st.date_input("Date", value="today", max_value="today")
day = selected.isoformat()
existing = get_goals_for_date(day) or {}

with st.form("goals_form"):
    calorie_target = st.number_input(
        "Calorie target",
        min_value=0.0,
        value=float(existing.get("calorie_target", 0)),
        step=1.0,
        key=f"cal_{day}",
    )
    protein_target = st.number_input(
        "Protein target (g)",
        min_value=0.0,
        value=float(existing.get("protein_target", 0)),
        step=1.0,
        key=f"pro_{day}",
    )
    carbs_target = st.number_input(
        "Carbs target (g)",
        min_value=0.0,
        value=float(existing.get("carbs_target", 0)),
        step=1.0,
        key=f"carb_{day}",
    )
    fats_target = st.number_input(
        "Fats target (g)",
        min_value=0.0,
        value=float(existing.get("fats_target", 0)),
        step=1.0,
        key=f"fat_{day}",
    )
    submitted = st.form_submit_button("Save")

if submitted:
    if calorie_target <= 0:
        st.warning("Enter a calorie target.")
    else:
        upsert_goals(
            Goals(
                date=day,
                calorie_target=calorie_target,
                protein_target=protein_target,
                carbs_target=carbs_target,
                fats_target=fats_target,
            )
        )
        st.success("Goals saved.")
