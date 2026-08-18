from services.db import get_entries_for_date, get_goals

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


def format_weight(grams: float, unit: str) -> str:
    """Format stored grams using the unit they were logged in."""
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


def macros_from_entries(entries: list[dict]) -> dict:
    """Sum entries and compare them to saved goals."""
    totals = sum_macros(entries)
    goals = get_goals()
    if not goals:
        return {"eaten": totals, "targets": None, "remaining": None, "pct": None}
    return compare_to_goals(totals, goals)


def macros_for_date(date: str) -> dict:
    """Sum that day's logged entries and compare them to saved goals."""
    return macros_from_entries(get_entries_for_date(date))
