from rest_framework import serializers
from recipe.models.recipe_user_model import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")
