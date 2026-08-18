from models.schemas import NutritionLabel
from services.gemini import generate

_PROMPT = (
    "Read the nutrition facts panel. Extract serving size, serving unit "
    "(g or oz only), and per-serving calories, protein, carbs, and fats. "
    "Use grams when the gram weight is printed. Do not guess a product name. "
    "Set found_label to false if this is not a readable nutrition facts label."
)


def read_label(image_bytes: bytes, mime_type: str) -> NutritionLabel:
    return generate(_PROMPT, NutritionLabel, image_bytes, mime_type)
