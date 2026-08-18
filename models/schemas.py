from dataclasses import dataclass, field
from typing import Literal, Optional


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
