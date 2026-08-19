import streamlit as st
from services.calculations import format_weight, macros_from_entries
from services.db import delete_logged_entry, get_entries_for_date

st.set_page_config(page_title="Daily Summary", layout="centered")
st.title("Daily Summary")


@st.dialog("Are you sure?")
def confirm_delete_log(entry_id: str, name: str, day: str) -> None:
    st.write(f"Delete **{name}** from the **{day}** log?")
    with st.container(horizontal=True):
        if st.button("Cancel", key="log_del_cancel"):
            st.rerun()
        if st.button("Delete", type="primary", key="log_del_ok"):
            delete_logged_entry(entry_id)
            st.rerun()

selected = st.date_input("Date", value="today", max_value="today")
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
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(
                f"**{name}** — {format_weight(float(entry['weight_grams']), entry.get('weight_unit') or 'g')}, "
                f"{float(entry['calories']):.0f} cal"
            )
            if st.button("Delete", key=f"del_{entry['id']}"):
                to_delete = (entry["id"], name)
    if to_delete:
        confirm_delete_log(*to_delete, day)
