from django.db import models
from users.models import User
from recipe.models.tag import Tag
from recipe.models.ingredient import Ingredient


# Модель рецепта
class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/recipes/')
    description = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')
    tags = models.ManyToManyField(Tag)
    cooking_time = models.IntegerField()

    def __str__(self):
        return self.title


# Модель ингредиента в рецепте
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.IntegerField()
