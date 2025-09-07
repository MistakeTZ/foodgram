from api.serializers.ingredient import IngredientSerializer
from api.serializers.short_recipe import ShortRecipeSerializer
from api.serializers.tag import TagSerializer
from recipe.models.recipe import Recipe, RecipeIngredient
from recipe.models.ingredient import Ingredient
from recipe.models.tag import Tag
from rest_framework import serializers
from users.serializers import UserSerializer
from django.core.files.base import ContentFile
import base64
from uuid import uuid4


class Base64ImageField(serializers.ImageField):
    """
    Поле для работы с base64 изображениями.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
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
        fields = ['name', 'text', 'cooking_time',
                  'image', 'ingredients', 'tags']

    def create(self, validated_data):
        validated_data['author'] = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item['id'])
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient, amount=item['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            for item in ingredients_data:
                ingredient = Ingredient.objects.get(id=item['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=item['amount']
                )
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
            "cooking_time",
        ]

    def get_ingredients(self, obj):
        return IngredientSerializer(
            obj.ingredients.all(), many=True, context={"recipe": obj}
        ).data


# Сериализатор пользователя с рецептами
class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    recipes = ShortRecipeSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["recipes", "recipes_count"]
