from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


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


class MacroSet(BaseModel):
    calories: float = Field(default=0, ge=0, description="Calories.")
    protein: float = Field(default=0, ge=0, description="Protein grams.")
    carbs: float = Field(default=0, ge=0, description="Carbohydrate grams.")
    fats: float = Field(default=0, ge=0, description="Fat grams.")


class EstimateComponent(BaseModel):
    name: str = Field(description="Visible part of the dish, e.g. rice noodles or broth.")
    grams: float = Field(gt=0, description="Grams of this part.")
    calories: float = Field(ge=0, description="Calories for this part's grams.")
    protein: float = Field(ge=0, description="Protein grams for this part.")
    carbs: float = Field(ge=0, description="Carb grams for this part.")
    fats: float = Field(ge=0, description="Fat grams for this part.")


class FoodEstimate(BaseModel):
    is_food: bool = Field(description="True only if the image shows edible food.")
    name: str = Field(default="", description="Dish name. Empty if not food.")
    total_grams: float = Field(
        default=0, ge=0, description="Total food grams for this portion, not the dishware."
    )
    components: list[EstimateComponent] = Field(default_factory=list)
    totals: MacroSet = Field(default_factory=MacroSet)
    per_100g: MacroSet = Field(default_factory=MacroSet)
    reasoning: str = Field(
        default="",
        description="Short explanation of the gram split and calorie guesses.",
    )

    @model_validator(mode="after")
    def food_must_have_portion(self) -> "FoodEstimate":
        if not self.is_food:
            return self
        if not self.name.strip():
            raise ValueError("name required when is_food is true")
        if self.total_grams <= 0:
            raise ValueError("total_grams must be > 0 when is_food is true")
        if not self.components:
            self.components = [
                EstimateComponent(
                    name=self.name.strip(),
                    grams=self.total_grams,
                    calories=self.totals.calories,
                    protein=self.totals.protein,
                    carbs=self.totals.carbs,
                    fats=self.totals.fats,
                )
            ]
        return self


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
