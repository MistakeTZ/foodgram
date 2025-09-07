from http import HTTPStatus

from api.serializers.recipe import RecipeSerializer
from django.db.models import Exists, OuterRef
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404
from recipe.models.recipe import Recipe
from recipe.models.recipe_user_model import Favorite, Cart
from recipe.recipes import create_recipe, get_recipes, update_recipe
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from users.auth import auth_user


# Работа с рецептами
class RecipesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    # Получение списка рецептов
    def get(self, request):
        request = auth_user(request)

        # Получение списка рецептов
        return get_recipes(request)

    # Создание рецепта
    def post(self, request):
        # Аутенификация по токену
        auth = TokenAuthentication()
        user_auth_tuple = auth.authenticate(request)
        if not user_auth_tuple:
            return JsonResponse(
                {"error": "Invalid token"}, status=HTTPStatus.UNAUTHORIZED
            )
        request.user, request.auth = user_auth_tuple

        # Проверка разрешения
        if not IsAuthenticated().has_permission(request, self):
            return JsonResponse(
                {"error": "Permission denied"}, status=HTTPStatus.UNAUTHORIZED
            )

        # Создание рецепта
        return create_recipe(request)


# Работа с конкретным рецептом
class RecipeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    # Получение конкретного рецепта
    def get_object(self, recipe_id, request):
        if request.user.is_authenticated:
            recipe = Recipe.objects.annotate(
                is_in_shopping_cart=Exists(
                    Cart.objects.filter(user=request.user,
                                        recipe=OuterRef('pk'))
                ),
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=request.user, recipe=OuterRef('pk'))
                )
            ).filter(id=recipe_id).first()
        else:
            recipe = Recipe.objects.annotate(
                is_in_shopping_cart=Exists(Cart.objects.none()),
                is_favorited=Exists(Favorite.objects.none())
            ).filter(id=recipe_id).first()

        if recipe:
            print(recipe.is_favorited)
            return recipe
        raise Http404("Recipe not found")

    # Получение конкретного рецепта
    def get(self, request, recipe_id):
        request = auth_user(request)

        recipe = self.get_object(recipe_id, request)
        return JsonResponse(RecipeSerializer(
            recipe,
            context={"request": request}
        ).data)

    # Обновление конкретного рецепта
    def patch(self, request, recipe_id):
        return self._update_or_delete(request, recipe_id, method="PATCH")

    # Удаление конкретного рецепта
    def delete(self, request, recipe_id):
        return self._update_or_delete(request, recipe_id, method="DELETE")

    # Обновление или удаление конкретного рецепта
    def _update_or_delete(self, request, recipe_id, method):
        # Получение токена
        auth = TokenAuthentication()
        try:
            user_auth_tuple = auth.authenticate(request)
            if not user_auth_tuple:
                raise AuthenticationFailed
        except AuthenticationFailed:
            return JsonResponse(
                {"error": "Invalid token"}, status=HTTPStatus.UNAUTHORIZED
            )

        request.user, request.auth = user_auth_tuple

        # Проверка авторизации
        if not IsAuthenticated().has_permission(request, self):
            return JsonResponse(
                {"error": "Permission denied"}, status=HTTPStatus.UNAUTHORIZED
            )

        # Проверка владельца
        recipe = self.get_object(recipe_id, request)
        if recipe.author != request.user:
            return JsonResponse(
                {"error": "No permission"},
                status=HTTPStatus.FORBIDDEN
            )

        # Обновление или удаление
        if method == "DELETE":
            recipe.delete()
            return HttpResponse(status=HTTPStatus.NO_CONTENT)
        elif method == "PATCH":
            return update_recipe(request, recipe)
