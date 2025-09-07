from django.http import JsonResponse, HttpResponse
from recipe.models.recipe import Recipe
from api.serializers.recipe import RecipeSerializer
from recipe.recipes import create_recipe, get_recipes, update_recipe
from django.shortcuts import get_object_or_404
from users.auth import auth_user
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed


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
            return JsonResponse({"error": "Invalid token"}, status=401)
        request.user, request.auth = user_auth_tuple

        # Проверка разрешения
        if not IsAuthenticated().has_permission(request, self):
            return JsonResponse({"error": "Permission denied"}, status=401)

        # Создание рецепта
        return create_recipe(request)


# Работа с конкретным рецептом
class RecipeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    # Получение конкретного рецепта
    def get_object(self, recipe_id):
        return get_object_or_404(Recipe, id=recipe_id)

    # Получение конкретного рецепта
    def get(self, request, recipe_id):
        recipe = self.get_object(recipe_id)
        return JsonResponse(
            RecipeSerializer(recipe, context={"request": request}).data
        )

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
            return JsonResponse({"error": "Invalid token"}, status=401)

        request.user, request.auth = user_auth_tuple

        # Проверка авторизации
        if not IsAuthenticated().has_permission(request, self):
            return JsonResponse({"error": "Permission denied"}, status=401)

        # Проверка владельца
        recipe = self.get_object(recipe_id)
        if recipe.author != request.user:
            return JsonResponse({"error": "No permission"}, status=403)

        # Обновление или удаление
        if method == "DELETE":
            recipe.delete()
            return HttpResponse(status=204)
        elif method == "PATCH":
            return update_recipe(request, recipe)
