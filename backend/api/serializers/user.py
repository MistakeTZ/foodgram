from rest_framework import serializers
from users.models import User
from recipe.models.recipe import Recipe
from users.models import Subscribtion
from api.serializers.short_recipe import ShortRecipeSerializer


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
        return Subscribtion.objects.filter(
            author=obj,
            user=self.context["request"].user).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


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
