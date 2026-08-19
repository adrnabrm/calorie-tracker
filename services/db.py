from supabase import create_client, Client
from utils.config import SUPABASE_URL, SUPABASE_KEY
from models.schemas import Food, Meal, MealIngredient, LoggedEntry, WeightLog, Goals

_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Foods ──────────────────────────────────────────────────────────────────────

def insert_food(food: Food) -> dict:
    row = {
        "name": food.name,
        "calories": food.calories,
        "protein": food.protein,
        "carbs": food.carbs,
        "fats": food.fats,
        "serving_grams": food.serving_grams,
        "serving_unit": food.serving_unit,
        "source": food.source,
    }
    res = _client.table("foods").insert(row).execute()
    return res.data[0]


def get_food_by_id(food_id: str) -> dict | None:
    res = _client.table("foods").select("*").eq("id", food_id).execute()
    return res.data[0] if res.data else None


def search_foods(query: str) -> list[dict]:
    res = (
        _client.table("foods")
        .select("*")
        .ilike("name", f"%{query}%")
        .order("name")
        .execute()
    )
    return res.data


def get_all_foods() -> list[dict]:
    res = _client.table("foods").select("*").order("name").execute()
    return res.data


def delete_food(food_id: str) -> None:
    _client.table("logged_entries").update({"food_id": None}).eq("food_id", food_id).execute()
    _client.table("foods").delete().eq("id", food_id).execute()


# ── Meals ──────────────────────────────────────────────────────────────────────

def insert_meal(meal: Meal) -> dict:
    row = {"name": meal.name, "type": meal.type}
    res = _client.table("meals").insert(row).execute()
    return res.data[0]


def get_meal_by_id(meal_id: str) -> dict | None:
    res = _client.table("meals").select("*").eq("id", meal_id).execute()
    return res.data[0] if res.data else None


def get_all_meals() -> list[dict]:
    res = _client.table("meals").select("*").order("name").execute()
    return res.data


# ── Meal Ingredients ───────────────────────────────────────────────────────────

def insert_meal_ingredient(ingredient: MealIngredient) -> dict:
    row = {
        "meal_id": ingredient.meal_id,
        "food_id": ingredient.food_id,
        "weight_grams": ingredient.weight_grams,
    }
    res = _client.table("meal_ingredients").insert(row).execute()
    return res.data[0]


def get_ingredients_for_meal(meal_id: str) -> list[dict]:
    res = (
        _client.table("meal_ingredients")
        .select("*, foods(*)")
        .eq("meal_id", meal_id)
        .execute()
    )
    return res.data


# ── Logged Entries ─────────────────────────────────────────────────────────────

def insert_logged_entry(entry: LoggedEntry) -> dict:
    row = {
        "date": entry.date,
        "food_id": entry.food_id,
        "meal_id": entry.meal_id,
        "weight_grams": entry.weight_grams,
        "calories": entry.calories,
        "protein": entry.protein,
        "carbs": entry.carbs,
        "fats": entry.fats,
        "weight_unit": entry.weight_unit,
    }
    res = _client.table("logged_entries").insert(row).execute()
    return res.data[0]


def get_entries_for_date(date: str) -> list[dict]:
    res = (
        _client.table("logged_entries")
        .select("*, foods(name, source)")
        .eq("date", date)
        .order("created_at")
        .execute()
    )
    return res.data


def delete_logged_entry(entry_id: str) -> None:
    _client.table("logged_entries").delete().eq("id", entry_id).execute()


# ── Weight Logs ────────────────────────────────────────────────────────────────

def upsert_weight_log(log: WeightLog) -> dict:
    existing = (
        _client.table("weight_logs")
        .select("id")
        .eq("date", log.date)
        .limit(1)
        .execute()
    )
    if existing.data:
        res = (
            _client.table("weight_logs")
            .update({"weight": log.weight})
            .eq("id", existing.data[0]["id"])
            .execute()
        )
        return res.data[0]
    res = (
        _client.table("weight_logs")
        .insert({"date": log.date, "weight": log.weight})
        .execute()
    )
    return res.data[0]


def get_all_weight_logs() -> list[dict]:
    res = _client.table("weight_logs").select("*").order("date").execute()
    return res.data


def delete_weight_log(log_id: str) -> None:
    _client.table("weight_logs").delete().eq("id", log_id).execute()


# ── Goals ──────────────────────────────────────────────────────────────────────

def upsert_goals(goals: Goals) -> dict:
    row = {
        "date": goals.date,
        "calorie_target": goals.calorie_target,
        "protein_target": goals.protein_target,
        "carbs_target": goals.carbs_target,
        "fats_target": goals.fats_target,
    }
    existing = (
        _client.table("goals")
        .select("id")
        .eq("date", goals.date)
        .limit(1)
        .execute()
    )
    if existing.data:
        res = (
            _client.table("goals")
            .update(row)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
        return res.data[0]
    res = _client.table("goals").insert(row).execute()
    return res.data[0]


def get_goals_for_date(date: str) -> dict | None:
    res = (
        _client.table("goals")
        .select("*")
        .lte("date", date)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None
