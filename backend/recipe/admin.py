from django.contrib import admin
from . import models

# Регистрация тега
admin.site.register(models.tag.Tag)


# Регистрация ингредиента
@admin.register(models.ingredient.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)


# Регистрация рецепта
class RecipeIngredientInline(admin.TabularInline):
    model = models.recipe.RecipeIngredient
    extra = 1


@admin.register(models.recipe.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('title', 'author', 'cooking_time', 'added_in_favorites')
    search_fields = ('title', 'author__username', 'author__email')
    list_filter = ('tags',)

    def added_in_favorites(self, obj):
        count = models.favorite.Favorite.objects.filter(recipe=obj).count()
        return count


# Регистрация избранного
admin.site.register(models.favorite.Favorite)
# Регистрация корзины
admin.site.register(models.cart.Cart)
