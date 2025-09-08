from http import HTTPStatus

from api.serializers import ShortRecipeSerializer
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from recipe.models.recipe import Recipe


def handle_user_recipe_relation(request, recipe_id, serializer_class,
                                already_exists_msg="Рецепт уже добавлен",
                                not_in_relation_msg="Рецепт не в списке"):
    recipe = Recipe.objects.filter(id=recipe_id).first()
    if not recipe:
        return JsonResponse(
            {"error": "Рецепт не найден"},
            status=HTTPStatus.NOT_FOUND
        )

    if request.method == "POST":
        try:
            serializer = serializer_class(
                data={"user": request.user.id, "recipe": recipe_id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except IntegrityError:
            return JsonResponse(
                {"field_name": [already_exists_msg]},
                status=HTTPStatus.BAD_REQUEST
            )
        return JsonResponse(
            ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED
        )

    if request.method == "DELETE":
        deleted, _ = serializer_class.Meta.model.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not deleted:
            return JsonResponse(
                {"error": not_in_relation_msg},
                status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
