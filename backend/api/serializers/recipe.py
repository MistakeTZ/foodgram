from rest_framework import serializers
from recipe.models.recipe import Recipe
from recipe.models.recipe_user_model import Favorite
from recipe.models.recipe_user_model import Cart
from api.serializers.short_recipe import ShortRecipeSerializer
from users.serializers import UserSerializer
from api.serializers.tag import TagSerializer
from api.serializers.ingredient import IngredientSerializer


# Сериализатор рецепта
class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        # Поля, которые возвращаются сериализатором
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time"
        ]

    # Поля, которые возвращаются сериализатором
    def get_is_favorited(self, obj):
        if not self.context["request"].user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=self.context["request"].user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if not self.context["request"].user.is_authenticated:
            return False
        return Cart.objects.filter(
            user=self.context["request"].user, recipe=obj).exists()

    def get_ingredients(self, obj):
        return IngredientSerializer(
            obj.ingredients.all(),
            many=True,
            context={"recipe": obj}
        ).data


# Сериализатор пользователя с рецептами
class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    recipes = ShortRecipeSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["recipes", "recipes_count"]
