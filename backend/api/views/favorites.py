from http import HTTPStatus

from api.serializers.short_recipe import ShortRecipeSerializer
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from recipe.models.recipe import Recipe
from recipe.models.recipe_user_model import Favorite
from rest_framework.decorators import api_view
from api.serializers.favorite import FavoriteSerializer


@api_view(["POST", "DELETE"])
def favorite(request, recipe_id):
    recipe = Recipe.objects.filter(id=recipe_id).first()

    if not recipe:
        return JsonResponse(
            {"error": "Рецепт не найден"},
            status=HTTPStatus.NOT_FOUND
        )

    if request.method == "POST":
        try:
            favorite = FavoriteSerializer(
                data={
                    "user": request.user.id,
                    "recipe": recipe_id
                }
            )
            favorite.is_valid(raise_exception=True)
            favorite.save()
        except IntegrityError:
            return JsonResponse(
                {"field_name": ["Рецепт уже в избранном"]},
                status=HTTPStatus.BAD_REQUEST,
            )
        return JsonResponse(
            ShortRecipeSerializer(recipe).data, status=HTTPStatus.CREATED
        )

    if request.method == "DELETE":
        deleted, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not deleted:
            return JsonResponse(
                {"error": "Рецепт не в избранном"},
                status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
