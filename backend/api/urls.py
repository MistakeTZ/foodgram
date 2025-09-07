from django.urls import path
from . import views


urlpatterns = [
    path('users/<int:user_id>/', views.users.get_user, name='user'),
    path('users/me/', views.users.me, name='me'),
    path('users/me/avatar/', views.avatar.avatar, name='avatar'),
    path('users/', views.users.UserListView.as_view(), name='users'),

    path('users/set_password/', views.login.set_password, name='set_password'),
    path('auth/token/login/', views.login.login, name='login'),
    path('auth/token/logout/', views.login.logout, name='logout'),

    path('users/subscriptions/',
         views.subscription.subscribtions, name='subscribtions'),
    path('users/<int:author_id>/subscribe/',
         views.subscription.subscribe, name='subscribe'),

    path('recipes/', views.recipes.RecipesView.as_view(), name='recipes'),
    path('recipes/<int:recipe_id>/',
         views.recipes.RecipeView.as_view(), name='recipe'),
    path('recipes/<int:recipe_id>/get-link/',
         views.link.get_link, name='get_link'),

    path('tags/', views.tags.tags, name='tags'),
    path('tags/<int:tag_id>/', views.tags.tag, name='tag'),

    path('ingredients/', views.ingredients.ingredients, name='ingredients'),
    path('ingredients/<int:ingredient_id>/',
         views.ingredients.ingredient, name='ingredient'),

    path('recipes/<int:recipe_id>/favorite/',
         views.favorites.favorite, name='favorite'),

    path('recipes/<int:recipe_id>/shopping_cart/',
         views.cart.shopping_cart, name='shopping_cart'),
    path('recipes/download_shopping_cart/',
         views.cart.download_shopping_cart, name='download_shopping_cart'),
]
