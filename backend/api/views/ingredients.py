from http import HTTPStatus

from api.filters import IngredientFilter
from api.serializers import IngredientSingleSerializer
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from recipe.models.ingredient import Ingredient
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny


class IngredientListView(ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSingleSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = None

    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    ordering_fields = ["name"]
    ordering = ["name"]


@require_GET
def ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.filter(id=ingredient_id).first()
    if not ingredient:
        return JsonResponse(
            {"field_name": ["Ингредиент не найден"]},
            status=HTTPStatus.BAD_REQUEST
        )
    return JsonResponse(IngredientSingleSerializer(ingredient).data)
