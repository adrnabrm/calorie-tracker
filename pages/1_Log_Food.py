from datetime import date
from typing import Literal

import streamlit as st
from models.schemas import Food, LoggedEntry, Meal, MealIngredient
from services.calculations import format_weight, scale_macros, to_grams
from services.db import (
    delete_food,
    delete_meal,
    get_all_foods,
    get_all_meals,
    get_ingredients_for_meal,
    insert_food,
    insert_logged_entry,
    insert_meal,
    insert_meal_ingredient,
)
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


@st.dialog("Are you sure?")
def confirm_delete_recipe(meal_id: str, name: str) -> None:
    st.write(f"Delete **{name}**? Past log entries will keep their macro data.")
    with st.container(horizontal=True):
        if st.button("Cancel"):
            st.rerun()
        if st.button("Delete", type="primary"):
            delete_meal(meal_id)
            load_recipes.clear()
            st.rerun()


@st.cache_data(ttl=60)
def load_foods() -> list[dict]:
    return get_all_foods()


@st.cache_data(ttl=60)
def load_recipes() -> list[dict]:
    return get_all_meals()


def _add_recipe_ingredient() -> None:
    new_id = st.session_state.recipe_next_id
    st.session_state.recipe_ingredient_ids.append(new_id)
    st.session_state.recipe_next_id += 1


def _remove_recipe_ingredient(rid: int) -> None:
    if rid in st.session_state.recipe_ingredient_ids:
        st.session_state.recipe_ingredient_ids.remove(rid)


def _editor_rows(edited) -> list[dict]:
    records = edited.to_dict("records") if hasattr(edited, "to_dict") else list(edited)
    return [r for r in records if float(r.get("grams") or 0) > 0]


st.session_state.setdefault("vision_estimate", None)
st.session_state.setdefault("vision_id", 0)
st.session_state.setdefault("vision_error", None)
st.session_state.setdefault("recipe_ingredient_ids", [0])
st.session_state.setdefault("recipe_next_id", 1)

library_tab, new_tab, photo_tab, recipes_tab = st.tabs(
    ["From library", "New food", "From photo", "Recipes"],
    on_change="rerun",
    key="log_food_tab",
)

with library_tab:
    if library_tab.open:
        query = st.text_input("Search")
        foods = load_foods()
        if query:
            q = query.lower()
            foods = [f for f in foods if q in f["name"].lower()]
        if not foods:
            st.info("No matching foods." if query else "No foods yet. Add one in New food.")
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

with new_tab:
    if new_tab.open:
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

with photo_tab:
    if photo_tab.open:
        camera = st.camera_input("Food photo")
        upload = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png", "webp"])
        image = camera or upload
        photo_weight = st.number_input(
            "Weight", min_value=0.0, value=0.0, step=1.0, key="vision_weight"
        )
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
                        "calories": st.column_config.NumberColumn(
                            "Calories", min_value=0.0, step=1.0
                        ),
                        "protein": st.column_config.NumberColumn(
                            "Protein", min_value=0.0, step=0.1
                        ),
                        "carbs": st.column_config.NumberColumn(
                            "Carbs", min_value=0.0, step=0.1
                        ),
                        "fats": st.column_config.NumberColumn(
                            "Fats", min_value=0.0, step=0.1
                        ),
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

with recipes_tab:
    if recipes_tab.open:
        recipes = load_recipes()
        if not recipes:
            st.info("No recipes yet. Create one below.")
        else:
            recipe_labels = {r["id"]: r["name"] for r in recipes}
            recipe_id = st.selectbox(
                "Recipe",
                list(recipe_labels.keys()),
                format_func=lambda i: recipe_labels[i],
                key="selected_recipe_id",
            )
            recipe = next(r for r in recipes if r["id"] == recipe_id)
            servings = int(recipe.get("servings") or 1)
            ingredients = get_ingredients_for_meal(recipe_id)
            batch_grams = 0.0
            batch_macros = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fats": 0.0}
            if ingredients:
                for ing in ingredients:
                    food = ing["foods"]
                    scaled = scale_macros(food, ing["weight_grams"])
                    for k in batch_macros:
                        batch_macros[k] += scaled[k]
                    batch_grams += ing["weight_grams"]
                    st.caption(f"{food['name']} — {ing['weight_grams']:g} g (batch)")
                serving_grams = batch_grams / servings
                serving_macros = {k: v / servings for k, v in batch_macros.items()}
                label = f"1 of {servings} servings" if servings > 1 else "1 serving"
                st.write(
                    f"**{serving_grams:g} g** ({label}) — "
                    f"{serving_macros['calories']:.0f} cal, "
                    f"{serving_macros['protein']:.0f}p / {serving_macros['carbs']:.0f}c / {serving_macros['fats']:.0f}f"
                )
            with st.container(horizontal=True):
                log_recipe_clicked = st.button("Log 1 serving", key="log_recipe_btn")
                del_recipe_clicked = st.button("Delete", key="del_recipe_btn")
            if log_recipe_clicked:
                if not ingredients:
                    st.warning("This recipe has no ingredients.")
                else:
                    insert_logged_entry(
                        LoggedEntry(
                            date=date.today().isoformat(),
                            meal_id=recipe_id,
                            food_id=None,
                            weight_grams=serving_grams,
                            calories=serving_macros["calories"],
                            protein=serving_macros["protein"],
                            carbs=serving_macros["carbs"],
                            fats=serving_macros["fats"],
                            weight_unit="g",
                        )
                    )
                    st.success("Logged.")
            if del_recipe_clicked:
                confirm_delete_recipe(recipe_id, recipe_labels[recipe_id])

        st.divider()
        st.subheader("Create a recipe")
        foods = load_foods()
        if not foods:
            st.info("No foods in library. Add some in New food first.")
        else:
            food_ids = [f["id"] for f in foods]
            food_labels = {f["id"]: f["name"] for f in foods}
            recipe_name = st.text_input("Recipe name", key="new_recipe_name")
            recipe_servings = st.number_input(
                "Servings (divide batch into this many portions)",
                min_value=1,
                value=1,
                step=1,
                key="new_recipe_servings",
            )
            food_map = {f["id"]: f for f in foods}
            for rid in list(st.session_state.recipe_ingredient_ids):
                cols = st.columns([4, 2, 2, 1])
                with cols[0]:
                    st.selectbox(
                        "Food",
                        food_ids,
                        format_func=lambda fid: food_labels[fid],
                        key=f"ri_food_{rid}",
                        label_visibility="collapsed",
                    )
                with cols[1]:
                    st.number_input(
                        "Amount",
                        min_value=0.1,
                        value=100.0,
                        step=1.0,
                        key=f"ri_amount_{rid}",
                        label_visibility="collapsed",
                    )
                with cols[2]:
                    st.segmented_control(
                        "Unit",
                        ["g", "oz"],
                        default="g",
                        key=f"ri_unit_{rid}",
                        label_visibility="collapsed",
                    )
                with cols[3]:
                    st.button(
                        ":material/close:",
                        key=f"ri_remove_{rid}",
                        on_click=_remove_recipe_ingredient,
                        args=(rid,),
                    )
                selected_fid = st.session_state.get(f"ri_food_{rid}")
                if selected_fid and selected_fid in food_map:
                    f = food_map[selected_fid]
                    st.caption(
                        f"{format_weight(float(f['serving_grams']), f.get('serving_unit') or 'g')} serving — "
                        f"{f['calories']:.0f} cal, {f['protein']:.0f}p / {f['carbs']:.0f}c / {f['fats']:.0f}f"
                    )
            with st.container(horizontal=True):
                st.button("Add ingredient", on_click=_add_recipe_ingredient)
                save_recipe_clicked = st.button("Save recipe", type="primary")
            if save_recipe_clicked:
                if not recipe_name.strip():
                    st.warning("Enter a recipe name.")
                elif not st.session_state.recipe_ingredient_ids:
                    st.warning("Add at least one ingredient.")
                else:
                    meal_row = insert_meal(
                        Meal(
                            name=recipe_name.strip(),
                            type="composed",
                            servings=int(recipe_servings),
                        )
                    )
                    for rid in st.session_state.recipe_ingredient_ids:
                        unit = st.session_state.get(f"ri_unit_{rid}") or "g"
                        insert_meal_ingredient(
                            MealIngredient(
                                meal_id=meal_row["id"],
                                food_id=st.session_state[f"ri_food_{rid}"],
                                weight_grams=to_grams(st.session_state[f"ri_amount_{rid}"], unit),
                            )
                        )
                    load_recipes.clear()
                    for rid in st.session_state.recipe_ingredient_ids:
                        st.session_state.pop(f"ri_food_{rid}", None)
                        st.session_state.pop(f"ri_amount_{rid}", None)
                        st.session_state.pop(f"ri_unit_{rid}", None)
                    st.session_state.recipe_ingredient_ids = [0]
                    st.session_state.recipe_next_id = 1
                    st.success(f"Recipe '{recipe_name.strip()}' saved.")
