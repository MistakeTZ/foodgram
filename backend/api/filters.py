import django_filters
from django.db.models import Case, IntegerField, Value, When
from recipe.models.ingredient import Ingredient


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method="filter_name")

    class Meta:
        model = Ingredient
        fields = ["name"]

    def filter_name(self, queryset, name, value):
        return (
            queryset.filter(name__icontains=value)
            .annotate(
                rank=Case(  # TODO: зачем это
                    When(name__istartswith=value, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            )
            .order_by("rank", "name")
        )
