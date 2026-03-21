# pyright: reportMissingImports=false
from lib_models.models import IngredientType
from pydantic import BaseModel, Field


class IngredientBase(BaseModel):
    ingredient_type: IngredientType
    quantity: int


class IngredientCreate(IngredientBase):
    pass


class Ingredient(IngredientBase):
    pass


class IngredientDecrease(BaseModel):
    ingredient_type: str
    quantity: int = Field(gt=0, description="Quantity to decrease, must be greater than zero")
