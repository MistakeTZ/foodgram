from http import HTTPStatus

from api.serializers.ingredient import IngredientSingleSerializer
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from recipe.models.ingredient import Ingredient
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView
from django.db.models import Case, When, Value, IntegerField


class IngredientListView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = IngredientSingleSerializer
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get("name")
        qs = Ingredient.objects.all()
        if not name:
            return qs
        return (
            qs.filter(name__icontains=name)
            .annotate(
                rank=Case(
                    When(name__istartswith=name, then=Value(0)),
                    When(name__icontains=name, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField()
                )
            )
            .order_by('rank', 'name')
        )


@require_GET
def ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.filter(id=ingredient_id).first()
    if not ingredient:
        return JsonResponse(
            {"field_name": ["Ингредиент не найден"]},
            status=HTTPStatus.BAD_REQUEST
        )
    return JsonResponse(IngredientSingleSerializer(ingredient).data)
