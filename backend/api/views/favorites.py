from rest_framework.decorators import api_view
from recipe.models.recipe import Recipe
from recipe.models.recipe_user_model import Favorite
from api.serializers.short_recipe import ShortRecipeSerializer
from django.http import JsonResponse, HttpResponse
from django.db.utils import IntegrityError


# Изменение списка избранного
@api_view(["POST", "DELETE"])
def favorite(request, recipe_id):
    recipe = Recipe.objects.filter(id=recipe_id).first()

    # Проверка существования рецепта
    if not recipe:
        return JsonResponse({"error": "Рецепт не найден"}, status=404)

    # Добавление рецепта в список
    if request.method == "POST":
        try:
            Favorite.objects.create(user=request.user, recipe=recipe)
        except IntegrityError:
            return JsonResponse({"field_name": ["Рецепт уже в избранном"]}, status=400)
        return JsonResponse(ShortRecipeSerializer(recipe).data, status=201)

    # Удаление рецепта из списка
    if request.method == "DELETE":
        is_deleted = Favorite.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not is_deleted[0]:
            return JsonResponse({"error": "Рецепт не в избранном"}, status=400)
        return HttpResponse(status=204)
