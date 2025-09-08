from app import constants
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(
        max_length=constants.MAX_INGREDIENT_NAME_LENGTH,
        verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=constants.MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"
