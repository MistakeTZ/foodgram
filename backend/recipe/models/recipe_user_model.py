from django.db import models
from users.models import User
from recipe.models.recipe import Recipe


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_recipe_relation",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="user_recipe_relation",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_user_recipe_relation",
            )
        ]

    def __str__(self):
        return f"{self.user.username} → {self.recipe.name}"


class Favorite(UserRecipeRelation):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite_relation",
            )
        ]


class Cart(UserRecipeRelation):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='carts')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='carts')

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_cart_relation",
            )
        ]
