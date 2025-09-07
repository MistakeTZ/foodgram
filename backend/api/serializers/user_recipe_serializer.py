from rest_framework import serializers
from recipe.models.recipe_user_model import Favorite, Cart


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ("user", "recipe")
