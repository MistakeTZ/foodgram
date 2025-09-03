from rest_framework import serializers
from django.contrib.auth.models import User
from recipe.models.recipe import Recipe
from .models import Subscribtion


# Сериализатор пользователя
class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Поля для сериализации
        fields = ["email", "id", "username", "first_name",
                  "last_name", "is_subscribed", "avatar"]

    # Получение полей
    def get_is_subscribed(self, obj):
        if not self.context["request"].user.is_authenticated:
            return False
        return Subscribtion.objects.filter(author=obj, user=self.context["request"].user).exists()

    def get_avatar(self, obj):
        if hasattr(obj, "profile") and obj.profile.avatar:
            return obj.profile.avatar.url
        return None


# Сериализатор короткого рецепта
class ShortRecipeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]

    def get_name(self, obj):
        return obj.title


# Сериализатор пользователя с рецептами
class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["recipes", "recipes_count"]

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return recipes.count()

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return ShortRecipeSerializer(recipes, many=True).data
