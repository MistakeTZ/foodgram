from django.db import models


# Модель ингредиента
class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"
