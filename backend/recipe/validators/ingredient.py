from pydantic import BaseModel, Field
from typing import List


# Валидатор ингредиентов
class Ingredient(BaseModel):
    id: int = Field(..., ge=0)
    amount: int = Field(..., ge=1)


class Data(BaseModel):
    ingredients: List[Ingredient]


def validate_ingredients(data: dict) -> Data:
    return Data.model_validate(data)
