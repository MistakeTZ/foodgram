from django.contrib import admin
from recipe import models


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "slug",)


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = models.RecipeIngredient
    extra = 1


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ("name", "author", "cooking_time", "added_in_favorites")
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("tags",)

    def added_in_favorites(self, obj):
        count = models.Favorite.objects.filter(
            recipe=obj
        ).count()
        return count


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
