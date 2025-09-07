from http import HTTPStatus

from api.serializers.short_recipe import ShortRecipeSerializer
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from recipe.models.recipe import Recipe
from recipe.models.recipe_user_model import Favorite
from rest_framework.decorators import api_view


# Изменение списка избранного
@api_view(["POST", "DELETE"])
def favorite(request, recipe_id):
    recipe = Recipe.objects.filter(id=recipe_id).first()

    # Проверка существования рецепта
    if not recipe:
        return JsonResponse(
            {"error": "Рецепт не найден"},
            status=HTTPStatus.NOT_FOUND
        )

    # Добавление рецепта в список
    if request.method == "POST":
        try:
            Favorite.objects.create(user=request.user, recipe=recipe)
        except IntegrityError:
            return JsonResponse(
                {"field_name": ["Рецепт уже в избранном"]},
                status=HTTPStatus.BAD_REQUEST,
            )
        return JsonResponse(
            ShortRecipeSerializer(recipe).data, status=HTTPStatus.CREATED
        )

    # Удаление рецепта из списка
    if request.method == "DELETE":
        is_deleted = Favorite.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not is_deleted[0]:
            return JsonResponse(
                {"error": "Рецепт не в избранном"},
                status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
