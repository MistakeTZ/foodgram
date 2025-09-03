from pydantic import BaseModel
from typing import List


# Валидация тегов
class Data(BaseModel):
    tags: List[int]


def validate_tags(data: dict) -> Data:
    return Data.model_validate(data)
