from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, Field


@dataclass
class Food:
    name: str
    calories: float
    protein: float
    carbs: float
    fats: float
    serving_grams: float
    serving_unit: Literal["g", "oz"]
    source: Literal["manual", "vision", "ocr", "estimated"]
    id: Optional[str] = None


class NutritionLabel(BaseModel):
    found_label: bool = Field(
        description="True only if the image is a readable nutrition facts panel."
    )
    serving_size: float = Field(
        description="Numeric serving size as printed. Use the gram weight when both a household measure and grams are shown."
    )
    serving_unit: Literal["g", "oz"] = Field(
        description="Unit for serving_size. Use g when grams are printed. Convert household units to g or oz only."
    )
    calories: float = Field(description="Calories per serving.")
    protein: float = Field(description="Protein grams per serving.")
    carbs: float = Field(description="Total carbohydrate grams per serving.")
    fats: float = Field(description="Total fat grams per serving.")


@dataclass
class Meal:
    name: str
    type: Literal["composed", "simple"]
    id: Optional[str] = None


@dataclass
class MealIngredient:
    meal_id: str
    food_id: str
    weight_grams: float


@dataclass
class LoggedEntry:
    date: str
    weight_grams: float
    calories: float
    protein: float
    carbs: float
    fats: float
    food_id: Optional[str] = None
    meal_id: Optional[str] = None
    weight_unit: Literal["g", "oz"] = "g"
    id: Optional[str] = None


@dataclass
class WeightLog:
    date: str
    weight: float
    id: Optional[str] = None


@dataclass
class Goals:
    calorie_target: float
    protein_target: float
    carbs_target: float
    fats_target: float
