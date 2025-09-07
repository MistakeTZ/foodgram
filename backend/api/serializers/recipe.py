from rest_framework import serializers
from recipe.models.recipe import Recipe
from recipe.models.favorite import Favorite
from recipe.models.cart import Cart
from api.serializers.user import UserSerializer
from api.serializers.tag import TagSerializer
from api.serializers.ingredient import IngredientSerializer


# Сериализатор рецепта
class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

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

    def get_name(self, obj):
        return obj.title

    def get_image(self, obj):
        return obj.image.url

    def get_text(self, obj):
        return obj.description

    def get_tags(self, obj):
        return TagSerializer(obj.tags.all(), many=True).data

    def get_author(self, obj):
        return UserSerializer(
            obj.author,
            context={"request": self.context["request"]}
        ).data

    def get_ingredients(self, obj):
        return IngredientSerializer(
            obj.ingredients.all(),
            many=True,
            context={"recipe": obj}
        ).data
