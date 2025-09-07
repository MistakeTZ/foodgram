from http import HTTPStatus

from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from recipe.models.recipe import Recipe


# Получение рецепта по короткой ссылке
@csrf_exempt
def short_link(request, link):
    recipe_id = int(link, 16)
    return redirect(f"/recipes/{recipe_id}")


# Создание короткой ссылки
@csrf_exempt
def get_link(request, recipe_id):
    recipe = Recipe.objects.filter(id=recipe_id).first()

    if not recipe:
        return JsonResponse(
            {"detail": "Recipe not found"},
            status=HTTPStatus.NOT_FOUND
        )

    # Генерация короткой ссылки
    link = hex(recipe.id)
    return JsonResponse(
        {"short-link": request.build_absolute_uri(
            reverse("short_link", args=[link]))},
        status=200,
    )
