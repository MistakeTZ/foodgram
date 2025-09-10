import django_filters
from django.db.models import Case, IntegerField, Value, When

from recipe.models import Cart, Favorite, Ingredient, Recipe


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method="filter_name")

    class Meta:
        model = Ingredient
        fields = ["name"]

    def filter_name(self, queryset, name, value):
        return (
            queryset.filter(name__icontains=value)
            .annotate(
                rank=Case(
                    When(name__istartswith=value, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
            )
            .order_by("rank", "name")
        )


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(field_name="author__id")
    tags = django_filters.CharFilter(method="filter_tags")
    is_favorited = django_filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = django_filters.BooleanFilter(
        method="filter_shopping_cart",
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_tags(self, queryset, name, value):
        """Кастомная фильтрация тегов с поддержкой множественных значений."""

        if not value:
            return queryset

        if "," in value:
            tags_list = [tag.strip() for tag in value.split(",")]
        else:
            tags_list = self.request.query_params.getlist("tags")
            if not tags_list:
                tags_list = [value]

        return queryset.filter(tags__slug__in=tags_list).distinct()

    def filter_favorited(self, queryset, name, value):
        """Фильтрация избранных рецептов."""

        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(
                id__in=Favorite.objects.filter(user=user).values_list(
                    "recipe_id", flat=True,
                ),
            )
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов в корзине."""

        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(
                id__in=Cart.objects.filter(user=user).values_list(
                    "recipe_id", flat=True,
                ),
            )
        return queryset
