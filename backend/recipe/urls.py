from django.urls import path
from .views import tags, recipes, ingredients, favorites, cart, link


urlpatterns = [
    path('recipes/', recipes.RecipesView.as_view(), name='recipes'),
    path('recipes/<int:recipe_id>/', recipes.RecipeView.as_view(), name='recipe'),
    path('recipes/<int:recipe_id>/get-link/', link.get_link, name='get_link'),

    path('tags/', tags.tags, name='tags'),
    path('tags/<int:tag_id>/', tags.tag, name='tag'),

    path('ingredients/', ingredients.ingredients, name='ingredients'),
    path('ingredients/<int:ingredient_id>/',
         ingredients.ingredient, name='ingredient'),

    path('recipes/<int:recipe_id>/favorite/',
         favorites.favorite, name='favorite'),

    path('recipes/<int:recipe_id>/shopping_cart/',
         cart.shopping_cart, name='shopping_cart'),
    path('recipes/download_shopping_cart/',
         cart.download_shopping_cart, name='download_shopping_cart'),
]
