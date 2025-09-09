from api import views
from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView, UserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("recipes", views.RecipeViewSet, basename="recipes")
router.register(r"users", views.UserViewSet, basename="users")
router.register("tags", views.TagViewSet, basename="tags")
router.register("ingredients", views.IngredientViewSet, basename="ingredients")


urlpatterns = [
    path(
        "users/set_password/",
        UserViewSet.as_view({"post": "set_password"}),
        name="set_password"
    ),
    path(
        "recipes/download_shopping_cart/",
        views.ShoppingCartViewSet.as_view({"get": "download"}),
        name="download_shopping_cart",
    ),
    path("", include(router.urls)),
    path("auth/token/login/", TokenCreateView.as_view(), name="login"),
    path("auth/token/logout/", TokenDestroyView.as_view(), name="logout"),
    path(
        "recipes/<int:recipe_id>/get-link/",
        views.ShortLinkViewSet.as_view({"get": "get_link"}),
        name="get_link"
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
]
