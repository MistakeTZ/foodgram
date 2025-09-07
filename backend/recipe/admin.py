from django.contrib import admin
from recipe import models


@admin.register(models.tag.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "slug",)


@admin.register(models.ingredient.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = models.recipe.RecipeIngredient
    extra = 1


@admin.register(models.recipe.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ("name", "author", "cooking_time", "added_in_favorites")
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("tags",)

    def added_in_favorites(self, obj):
        count = models.recipe_user_model.Favorite.objects.filter(
            recipe=obj
        ).count()
        return count


@admin.register(models.recipe_user_model.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")


@admin.register(models.recipe_user_model.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
