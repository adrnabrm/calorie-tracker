from services.db import get_goals_for_date

_KEYS = ("calories", "protein", "carbs", "fats")
OZ_TO_G = 28.3495
_GOAL_KEYS = {
    "calories": "calorie_target",
    "protein": "protein_target",
    "carbs": "carbs_target",
    "fats": "fats_target",
}


def to_grams(amount: float, unit: str) -> float:
    """Convert an amount in g or oz to grams."""
    return amount * OZ_TO_G if unit == "oz" else amount


def format_weight(grams: float, unit: str, serving_grams: float | None = None) -> str:
    """Format stored grams using the unit they were logged in."""
    if unit == "serving" and serving_grams:
        servings = grams / serving_grams
        label = "serving" if servings == 1 else "servings"
        return f"{servings:g} {label}"
    if unit == "oz":
        return f"{grams / OZ_TO_G:g} oz"
    return f"{grams:g} g"


def scale_macros(food: dict, eaten_grams: float) -> dict:
    """Scale a food's per-serving macros to the grams eaten."""
    factor = eaten_grams / float(food["serving_grams"])
    return {k: float(food[k]) * factor for k in _KEYS}


def sum_macros(entries: list[dict]) -> dict:
    """Add up calories, protein, carbs, and fats from a list of logged entries."""
    return {k: sum(float(e[k]) for e in entries) for k in _KEYS}


def compare_to_goals(totals: dict, goals: dict) -> dict:
    """Compare eaten macros to targets. Returns eaten, targets, remaining, and percent of target."""
    targets = {k: float(goals[_GOAL_KEYS[k]]) for k in _KEYS}
    return {
        "eaten": totals,
        "targets": targets,
        "remaining": {k: targets[k] - totals[k] for k in _KEYS},
        "pct": {k: (totals[k] / targets[k] * 100) if targets[k] else 0.0 for k in _KEYS},
    }


def macros_from_entries(entries: list[dict], date: str) -> dict:
    """Sum entries and compare them to the goals in effect on that date."""
    totals = sum_macros(entries)
    goals = get_goals_for_date(date)
    if not goals:
        return {"eaten": totals, "targets": None, "remaining": None, "pct": None}
    return compare_to_goals(totals, goals)
