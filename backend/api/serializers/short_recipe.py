from rest_framework import serializers
from recipe.models.recipe import Recipe


# Сериализатор короткого рецепта
class ShortRecipeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]

    def get_name(self, obj):
        return obj.title
