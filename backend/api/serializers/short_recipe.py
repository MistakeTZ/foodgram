from recipe.models.recipe import Recipe
from rest_framework import serializers


# Сериализатор короткого рецепта
class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]
