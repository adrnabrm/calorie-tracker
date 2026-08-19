from typing import Literal

from models.schemas import EstimateComponent, FoodEstimate, MacroSet
from services.gemini import generate

MODEL = "gemini-3.6-flash"
_KEYS = ("calories", "protein", "carbs", "fats")


def _rescale(estimate: FoodEstimate, target_grams: float) -> FoodEstimate:
    current = sum(c.grams for c in estimate.components)
    if current <= 0 or target_grams <= 0:
        return estimate
    factor = target_grams / current
    components = [
        EstimateComponent(
            name=c.name,
            grams=c.grams * factor,
            calories=c.calories * factor,
            protein=c.protein * factor,
            carbs=c.carbs * factor,
            fats=c.fats * factor,
        )
        for c in estimate.components
    ]
    totals = MacroSet(**{k: sum(getattr(c, k) for c in components) for k in _KEYS})
    per_100g = MacroSet(**{k: getattr(totals, k) / target_grams * 100 for k in _KEYS})
    return estimate.model_copy(
        update={
            "total_grams": target_grams,
            "components": components,
            "totals": totals,
            "per_100g": per_100g,
        }
    )


def estimate(
    image_bytes: bytes,
    mime_type: str,
    *,
    grams: float | None,
    size: Literal["small", "typical", "large"] | None,
    notes: str,
) -> FoodEstimate:
    parts = [
        "Estimate calories and macros for the food in this photo.",
        "This is a mixed dish. Split it into visible parts (broth, noodles, meat, etc.).",
        "Grams are food-only, not the bowl or plate.",
        "Component grams must add up to the portion grams.",
        "Always include at least one component. If you cannot split the dish, use one row for the whole portion.",
        "Set is_food to false if this image is not food.",
    ]
    if grams is not None:
        parts.append(f"The user weighed the food at {grams:g} grams. Use that as the total.")
    elif size:
        parts.append(
            f"No scale. Treat portion size as {size} for this kind of dish and guess total grams."
        )
    if notes.strip():
        parts.append(f"User notes: {notes.strip()}")
    result = generate(
        " ".join(parts),
        FoodEstimate,
        image_bytes,
        mime_type,
        model=MODEL,
        thinking_level="medium",
    )
    if result.is_food:
        target = grams if grams is not None else result.total_grams
        if target > 0:
            result = _rescale(result, target)
    return result
