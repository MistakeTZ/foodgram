from api import views
from django.urls import path

urlpatterns = [
    path("users/<int:user_id>/", views.UserView.as_view(), name="user"),
    path("users/me/", views.MeView.as_view(), name="me"),
    path("users/me/avatar/", views.avatar, name="avatar"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/set_password/", views.set_password, name="set_password"),
    path("auth/token/login/", views.login, name="login"),
    path("auth/token/logout/", views.logout, name="logout"),
    path(
        "users/subscriptions/",
        views.subscribtions,
        name="subscribtions"
    ),
    path(
        "users/<int:author_id>/subscribe/",
        views.SubscribeView.as_view(),
        name="subscribe",
    ),
    path("recipes/", views.RecipesView.as_view(), name="recipes"),
    path("recipes/<int:recipe_id>/",
         views.RecipeView.as_view(), name="recipe"),
    path("recipes/<int:recipe_id>/get-link/",
         views.get_link, name="get_link"),
    path("tags/", views.tags, name="tags"),
    path("tags/<int:tag_id>/", views.tag, name="tag"),
    path(
        "ingredients/",
        views.IngredientListView.as_view(),
        name="ingredients"
    ),
    path(
        "ingredients/<int:ingredient_id>/",
        views.ingredient,
        name="ingredient",
    ),
    path(
        "recipes/<int:recipe_id>/favorite/",
        views.favorite,
        name="favorite"
    ),
    path(
        "recipes/<int:recipe_id>/shopping_cart/",
        views.shopping_cart,
        name="shopping_cart",
    ),
    path(
        "recipes/download_shopping_cart/",
        views.download_shopping_cart,
        name="download_shopping_cart",
    ),
]
