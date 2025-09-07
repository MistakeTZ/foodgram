from rest_framework import serializers
from recipe.models.ingredient import Ingredient
from recipe.models.recipe import RecipeIngredient


# Сериализатор ингредиента
class IngredientSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit", "amount"]

    def get_amount(self, obj):
        return RecipeIngredient.objects.get(
            ingredient=obj, recipe=self.context["recipe"]).amount


# Сериализатор ингредиента
class IngredientSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]
