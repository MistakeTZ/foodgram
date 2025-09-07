from django.http import JsonResponse
from recipe.models.recipe import Recipe, RecipeIngredient
from recipe.models.recipe_user_model import Favorite
from recipe.models.recipe_user_model import Cart
from recipe.models.ingredient import Ingredient
from recipe.paginator import RecipePagination
from api.serializers.recipe import RecipeSerializer
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from recipe import validators
import json
import base64
from uuid import uuid4


# Создание рецепта
def create_recipe(request):
    # Проверка JSON
    data = check_fields(request.body)

    # Если проверка не прошла или отсутствует изображение
    if isinstance(data, str):
        return JsonResponse({"field_name": [data]}, status=400)
    if not data["image"]:
        return JsonResponse(
            {"field_name": ["Отсутствует изображение"]},
            status=400
        )

    try:
        # Создание рецепта
        new_recipe = Recipe.objects.create(
            author=request.user,
            title=data["name"],
            description=data["text"],
            cooking_time=data["cooking_time"],
            image=data["image"]
        )

        # Добавление ингредиентов и тегов
        new_recipe.tags.set(data["tags"])
        for item in data["ingredients"]:
            ingredient = Ingredient.objects.get(id=item["id"])
            RecipeIngredient.objects.create(
                recipe=new_recipe,
                ingredient=ingredient,
                amount=item["amount"]
            )
        new_recipe.save()

        return redirect("recipe", new_recipe.id)
    except Exception as e:
        return JsonResponse({"field_name": [str(e)]}, status=400)


# Получение рецептов
def get_recipes(request):
    # Параметры
    is_favorited = int(request.GET.get('is_favorited', 0))
    is_in_shopping_cart = int(request.GET.get('is_in_shopping_cart', 0))
    author = request.GET.get('author')
    tags = request.GET.getlist('tags')

    # Получение рецептов
    recipes = Recipe.objects.all()

    # Фильтрация
    if author:
        recipes = recipes.filter(author=author)
    if tags:
        recipes = recipes.filter(tags__slug__in=tags).distinct()

    # Фильтрация по избранному и в корзине
    if is_favorited:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Вы не авторизованы"}, status=401)

        favorites = Favorite.objects.filter(
            user=request.user).values_list("recipe_id", flat=True)
        recipes = recipes.filter(id__in=favorites)
    if is_in_shopping_cart:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Вы не авторизованы"}, status=401)

        cart = Cart.objects.filter(
            user=request.user).values_list("recipe_id", flat=True)
        recipes = recipes.filter(id__in=cart)

    # Сортировка
    recipes = recipes.order_by('-id')

    # Пагинация
    paginator = RecipePagination()
    recipes = paginator.paginate_queryset(recipes, request)

    return paginator.get_paginated_response(RecipeSerializer(
        recipes, many=True, context={"request": request}).data)


# Изменение рецепта
def update_recipe(request, recipe):
    # Проверка JSON
    data = check_fields(request.body)
    if isinstance(data, str):
        return JsonResponse({"field_name": [data]}, status=400)

    # Обновление рецепта
    recipe.title = data["name"]
    recipe.description = data["text"]
    recipe.cooking_time = data["cooking_time"]
    if data["image"]:
        recipe.image = data["image"]
    recipe.save()

    # Обновление ингредиентов и тегов
    recipe.tags.clear()
    recipe.tags.set(data["tags"])
    RecipeIngredient.objects.filter(recipe=recipe).delete()
    for item in data["ingredients"]:
        ingredient = Ingredient.objects.get(id=item["id"])
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount=item["amount"]
        )

    return JsonResponse(RecipeSerializer(
        recipe, context={"request": request}).data)


# Проверка JSON
def check_fields(body):
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return "Invalid JSON"

    # Проверка ингредиентов
    try:
        ingredients = data["ingredients"]
        validators.ingredient.validate_ingredients(data)
    except KeyError:
        return "Поле ingredients отсутствует"
    except ValueError as e:
        return str(e)

    # Проверка тегов
    try:
        tags = data["tags"]
        validators.tag.validate_tags(data)
    except KeyError:
        return "Поле tags отсутствует"
    except ValueError as e:
        return str(e)

    # Проверка изображения
    try:
        image = data.get("image")

        if image:
            format, imgstr = image.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"{uuid4()}.{ext}"
            content = ContentFile(base64.b64decode(imgstr), name=file_name)
        else:
            content = None
    except (ValueError, IndexError, base64.binascii.Error):
        return "Не удалось загрузить изображение"

    # Другие поля
    try:
        name = str(data["name"])
        text = str(data["text"])
        cooking_time = int(data["cooking_time"])
    except KeyError as e:
        return f"Поле {e.args[0]} отсутствует"
    except (TypeError, ValueError):
        return "Некорректные данные"

    # Возвращаем данные
    return {
        "name": name,
        "text": text,
        "cooking_time": cooking_time,
        "image": content,
        "ingredients": ingredients,
        "tags": tags
    }
