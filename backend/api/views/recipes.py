from http import HTTPStatus

from api.serializers.recipe import (
    RecipeSerializer, RecipeCreateUpdateSerializer
)
from django.db.models import Exists, OuterRef
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404
from django.shortcuts import redirect
from recipe.models.recipe import Recipe
from recipe.models.recipe_user_model import Favorite, Cart
from api.paginator import RecipePagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView


class RecipesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        request = auth_user(request)

        user = request.user
        recipes = Recipe.objects.all()

        if user.is_authenticated:
            recipes = recipes.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=user, recipe=OuterRef('pk'))),
                is_in_shopping_cart=Exists(Cart.objects.filter(
                    user=user, recipe=OuterRef('pk')))
            )
        else:
            recipes = recipes.annotate(
                is_favorited=Exists(Favorite.objects.none()),
                is_in_shopping_cart=Exists(Cart.objects.none())
            )

        author = request.GET.get("author")
        if author:
            recipes = recipes.filter(author=author)

        tags = request.GET.getlist("tags")
        if tags:
            recipes = recipes.filter(tags__slug__in=tags).distinct()

        if request.GET.get("is_favorited") == "1":
            if not user.is_authenticated:
                return JsonResponse(
                    {"error": "Вы не авторизованы"},
                    status=HTTPStatus.UNAUTHORIZED
                )
            favorites = Favorite.objects.filter(
                user=request.user
            ).values_list(
                "recipe_id", flat=True
            )
            recipes = recipes.filter(id__in=favorites)

        if request.GET.get("is_in_shopping_cart") == "1":
            if not user.is_authenticated:
                return JsonResponse(
                    {"error": "Вы не авторизованы"},
                    status=HTTPStatus.UNAUTHORIZED
                )
            cart = Cart.objects.filter(user=request.user).values_list(
                "recipe_id", flat=True
            )
            recipes = recipes.filter(id__in=cart)

        recipes = recipes.order_by("-id")

        paginator = RecipePagination()
        if request.GET.get("limit"):
            paginator.page_size = request.GET.get("limit")

        paginated = paginator.paginate_queryset(recipes, request)
        serializer = RecipeSerializer(
            paginated, many=True, context={"request": request})

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        auth = TokenAuthentication()
        user_auth_tuple = auth.authenticate(request)
        if not user_auth_tuple:
            return JsonResponse(
                {"error": "Invalid token"}, status=HTTPStatus.UNAUTHORIZED
            )
        request.user, request.auth = user_auth_tuple

        if not IsAuthenticated().has_permission(request, self):
            return JsonResponse(
                {"error": "Permission denied"}, status=HTTPStatus.UNAUTHORIZED
            )

        serializer = RecipeCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            recipe = serializer.save()
            return redirect("recipe", recipe.id)

        field_errors = [str(field[0]) for field in serializer.errors.values()]
        return JsonResponse(
            {"field_name": field_errors},
            status=HTTPStatus.BAD_REQUEST
        )


class RecipeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
            return recipe
        raise Http404("Recipe not found")

    def get(self, request, recipe_id):
        request = auth_user(request)

        recipe = self.get_object(recipe_id, request)
        return JsonResponse(RecipeSerializer(
            recipe,
            context={"request": request}
        ).data)

    def patch(self, request, recipe_id):
        return self._update_or_delete(request, recipe_id, method="PATCH")

    def delete(self, request, recipe_id):
        return self._update_or_delete(request, recipe_id, method="DELETE")

    def _update_or_delete(self, request, recipe_id, method):
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

        if not IsAuthenticated().has_permission(request, self):
            return JsonResponse(
                {"error": "Permission denied"}, status=HTTPStatus.UNAUTHORIZED
            )

        recipe = self.get_object(recipe_id, request)
        if recipe.author != request.user:
            return JsonResponse(
                {"error": "No permission"},
                status=HTTPStatus.FORBIDDEN
            )

        if method == "DELETE":
            recipe.delete()
            return HttpResponse(status=HTTPStatus.NO_CONTENT)
        elif method == "PATCH":
            serializer = RecipeCreateUpdateSerializer(
                recipe,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                recipe = serializer.save()
                output = RecipeSerializer(
                    recipe, context={'request': request}
                ).data
                return JsonResponse(output)

            field_errors = [str(field[0])
                            for field in serializer.errors.values()]
            return JsonResponse(
                {"field_name": field_errors},
                status=HTTPStatus.BAD_REQUEST
            )


def auth_user(request):
    auth = TokenAuthentication()
    try:
        user_auth_tuple = auth.authenticate(request)
        if user_auth_tuple:
            request.user, request.auth = user_auth_tuple
    except AuthenticationFailed:
        pass
    finally:
        return request
