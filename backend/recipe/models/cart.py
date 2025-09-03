from django.db import models
from django.contrib.auth.models import User
from .recipe import Recipe


# Список покупок
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
