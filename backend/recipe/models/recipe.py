from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from recipe.models.ingredient import Ingredient
from recipe.models.tag import Tag
from users.models import User


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes"
    )
    name = models.CharField(max_length=settings.MAX_RECIPE_TITLE_LENGTH)
    image = models.ImageField(upload_to="images/recipes/")
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient")
    tags = models.ManyToManyField(Tag)
    cooking_time = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Время приготовления в минутах"
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    amount = models.SmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"

    def __str__(self):
        return (
            f"{self.ingredient.name} "
            f"({self.amount} {self.ingredient.measurement_unit})"
        )
