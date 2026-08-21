from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from models.schemas import Food, LoggedEntry
from services.calculations import to_grams
from services.db import insert_food, insert_logged_entry
from services.gemini import GeminiError
from services.ocr import read_label

st.set_page_config(page_title="Scan Label", layout="centered")
st.title("Scan Nutrition Label")

st.session_state.setdefault("ocr_label", None)
st.session_state.setdefault("ocr_id", 0)
st.session_state.setdefault("ocr_error", None)

camera = st.camera_input("Label photo")
upload = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png", "webp"])
image = camera or upload

if st.button("Read label"):
    if not image:
        st.warning("Take or upload a photo first.")
    else:
        with st.spinner("Reading label"):
            try:
                st.session_state.ocr_label = read_label(
                    image.getvalue(), image.type or "image/jpeg"
                )
                st.session_state.ocr_id += 1
                st.session_state.ocr_error = None
            except GeminiError as e:
                st.session_state.ocr_label = None
                st.session_state.ocr_error = str(e)

if st.session_state.ocr_error:
    st.error(st.session_state.ocr_error)
    st.stop()

label = st.session_state.ocr_label
if label is None:
    st.stop()

if not label.found_label:
    st.error("No nutrition label found.")
    st.stop()

ocr_id = st.session_state.ocr_id
_ocr_serving_unit = st.segmented_control(
    "Serving unit",
    ["g", "oz", "serving"],
    default=label.serving_unit,
    key=f"ocr_unit_{ocr_id}",
)
with st.form("confirm_ocr"):
    name = st.text_input("Name")
    if (_ocr_serving_unit or "g") != "serving":
        serving_size = st.number_input(
            "Serving size",
            min_value=0.1,
            value=max(float(label.serving_size), 0.1),
            step=1.0,
            key=f"ocr_serving_{ocr_id}",
        )
    else:
        serving_size = 100.0
    calories = st.number_input(
        "Calories (per serving)",
        min_value=0.0,
        value=float(label.calories),
        step=1.0,
        key=f"ocr_cal_{ocr_id}",
    )
    protein = st.number_input(
        "Protein (g, per serving)",
        min_value=0.0,
        value=float(label.protein),
        step=0.1,
        key=f"ocr_pro_{ocr_id}",
    )
    carbs = st.number_input(
        "Carbs (g, per serving)",
        min_value=0.0,
        value=float(label.carbs),
        step=0.1,
        key=f"ocr_carb_{ocr_id}",
    )
    fats = st.number_input(
        "Fats (g, per serving)",
        min_value=0.0,
        value=float(label.fats),
        step=0.1,
        key=f"ocr_fat_{ocr_id}",
    )
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("Save to library")
    with col2:
        save_and_log = st.form_submit_button("Save and log 1 serving", type="primary")

if submitted or save_and_log:
    if not name.strip():
        st.warning("Enter a name.")
    else:
        unit = _ocr_serving_unit or "g"
        sg = serving_size if unit == "serving" else to_grams(serving_size, unit)
        food_row = insert_food(
            Food(
                name=name.strip(),
                calories=calories,
                protein=protein,
                carbs=carbs,
                fats=fats,
                serving_grams=sg,
                serving_unit=unit,
                source="ocr",
            )
        )
        st.cache_data.clear()
        if save_and_log:
            today = datetime.now(ZoneInfo(st.context.timezone or "UTC")).date().isoformat()
            insert_logged_entry(
                LoggedEntry(
                    date=today,
                    food_id=food_row["id"],
                    weight_grams=sg,
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fats=fats,
                    weight_unit="serving",
                )
            )
            st.success("Saved and logged 1 serving.")
        else:
            st.success("Saved to library.")
