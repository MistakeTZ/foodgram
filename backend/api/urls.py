from api import views
from django.urls import path
from djoser.views import TokenCreateView, TokenDestroyView, UserViewSet

urlpatterns = [
    path("users/<int:user_id>/", views.UserView.as_view(), name="user"),
    path("users/me/", views.MeView.as_view(), name="me"),
    path("users/me/avatar/", views.avatar, name="avatar"),
    path("users/", views.UserListView.as_view(), name="users"),
    path(
        "users/set_password/",
        UserViewSet.as_view({"post": "set_password"}),
        name="set_password"
    ),
    path("auth/token/login/", TokenCreateView.as_view(), name="login"),
    path("auth/token/logout/", TokenDestroyView.as_view(), name="logout"),
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
    path(
        "recipes/",
        views.RecipeView.as_view(
            {"get": "get_recipes", "post": "post_recipe"}
        ),
        name="recipes"
    ),
    path(
        "recipes/<int:pk>/",
        views.RecipeView.as_view(
            {
                "get": "get_recipe",
                "patch": "update_or_delete",
                "delete": "update_or_delete"
            }
        ),
        name="recipe"
    ),
    path(
        "recipes/<int:recipe_id>/get-link/",
         views.ShortLinkViewSet.as_view({"get": "get_link"}),
         name="get_link"
    ),
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
        "recipes/<int:pk>/shopping_cart/",
        views.ShoppingCartViewSet.as_view(
            {"post": "recipes", "delete": "recipes"}
        ),
        name="shopping_cart",
    ),
    path(
        "recipes/download_shopping_cart/",
        views.ShoppingCartViewSet.as_view({"get": "download"}),
        name="download_shopping_cart",
    ),
]
