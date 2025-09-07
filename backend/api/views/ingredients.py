from http import HTTPStatus

from api.serializers.ingredient import IngredientSingleSerializer
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from recipe.models.ingredient import Ingredient


# Получение списка ингредиентов
@require_GET
def ingredients(request):
    name = request.GET.get("name", "")

    # Проверка ввода
    if name:
        ingredient_list = (
            Ingredient.objects.annotate(
                starts_with_name=Case(
                    When(name__istartswith=name, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .filter(Q(name__icontains=name))
            .order_by("starts_with_name", "name")
        )
    else:
        ingredient_list = Ingredient.objects.all()

    # Сериализация
    serializer = IngredientSingleSerializer(ingredient_list, many=True)

    return JsonResponse(serializer.data, safe=False)


# Получение ингредиента
@require_GET
def ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.filter(id=ingredient_id).first()
    if not ingredient:
        return JsonResponse(
            {"field_name": ["Ингредиент не найден"]},
            status=HTTPStatus.BAD_REQUEST
        )
    return JsonResponse(IngredientSingleSerializer(ingredient).data)
