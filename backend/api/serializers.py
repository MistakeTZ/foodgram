import base64
import re
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from recipe.models.ingredient import Ingredient
from recipe.models.recipe import Recipe, RecipeIngredient
from recipe.models.recipe_user_model import Cart, Favorite
from recipe.models.tag import Tag
from rest_framework import serializers
from users.models import Subscribtion, User


class UserPasswordUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.instance
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль указан неверно.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def update(self, instance, validated_data):
        instance.set_password(
            make_password(validated_data["new_password"])
        )
        instance.save(update_fields=["password"])
        return instance


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
            "avatar",
        ]

    def validate_username(self, value):
        valid = re.compile(r"^[\w.@+-]+\Z")

        if not valid.match(value):
            raise serializers.ValidationError("Username некорректный")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def get_is_subscribed(self, obj):
        if not self.context["request"].user.is_authenticated:
            return False
        return Subscribtion.objects.filter(
            author=obj, user=self.context["request"].user
        ).exists()

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]


class IngredientSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit", "amount"]

    def get_amount(self, obj):
        return RecipeIngredient.objects.get(
            ingredient=obj, recipe=self.context["recipe"]
        ).amount


class IngredientSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class Base64ImageField(serializers.ImageField):
    """Поле для работы с base64 изображениями."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                format, imgstr = data.split(";base64,")
                ext = format.split("/")[-1]
                file_name = f"{uuid4()}.{ext}"
                data = ContentFile(base64.b64decode(imgstr), name=file_name)
            except (ValueError, IndexError, TypeError, base64.binascii.Error):
                raise serializers.ValidationError(
                    "Не удалось загрузить изображение")
        return super().to_internal_value(data)


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов.
    Используется только для write операций.
    """
    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ["name", "text", "cooking_time",
                  "image", "ingredients", "tags"]

    def create_ingredients_and_tags(self, validated_data, recipe):
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe.tags.set(tags)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item["id"],
                amount=item["amount"]
            )
            for item in ingredients_data
        ]

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def create(self, validated_data):
        validated_data["author"] = self.context.get("request").user
        recipe = Recipe.objects.create(**validated_data)

        self.create_ingredients_and_tags(validated_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        super().update(instance, validated_data)

        self.create_ingredients_and_tags(validated_data, instance)
        return instance


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
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
            "cooking_time",
        ]

    def get_ingredients(self, obj):
        return IngredientSerializer(
            obj.ingredients.all(), many=True, context={"recipe": obj}
        ).data


class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    recipes = ShortRecipeSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["recipes", "recipes_count"]


class SubscribtionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribtion
        fields = ("author", "user")
        extra_kwargs = {"user": {"read_only": True}}


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ("user", "recipe")


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ["avatar"]
