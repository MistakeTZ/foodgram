from django.core.validators import MinValueValidator
from django.db import models
from slugify import slugify

from app import constants
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=constants.MAX_TAG_NAME_LENGTH,
        unique=True,
        verbose_name="Название",
    )
    slug = models.SlugField(
        max_length=constants.MAX_TAG_SLUG_LENGTH,
        unique=True,
        blank=True,
        verbose_name="Слаг",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=constants.MAX_INGREDIENT_NAME_LENGTH,
        verbose_name="Название ингредиента",
    )
    measurement_unit = models.CharField(
        max_length=constants.MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=constants.MAX_RECIPE_TITLE_LENGTH,
        verbose_name="Название",
    )
    image = models.ImageField(
        upload_to="images/recipes/",
        verbose_name="Изображение",
    )
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(Tag, verbose_name="Теги")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Время приготовления в минутах",
        verbose_name="Время приготовления",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="%(class)s_set",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_%(class)s_relation",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.recipe.name}"


class Favorite(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"


class Cart(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = "Корзина"
        verbose_name_plural = "Список покупок"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"

    def __str__(self):
        return (
            f"{self.ingredient.name} "
            f"({self.amount} {self.ingredient.measurement_unit})"
        )
