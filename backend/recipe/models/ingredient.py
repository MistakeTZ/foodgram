from django.db import models
from django.conf import settings


# Модель ингредиента
class Ingredient(models.Model):
    name = models.CharField(max_length=settings.MAX_INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        max_length=settings.MAX_MEASUREMENT_UNIT_LENGTH)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"
