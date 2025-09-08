import io
import json
import pathlib
from http import HTTPStatus

from api.filters import IngredientFilter
from api.paginator import PagePagination
from api.serializers import (
    AvatarSerializer,
    CartSerializer,
    FavoriteSerializer,
    IngredientSingleSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscribtionSerializer,
    TagSerializer,
    UserPasswordUpdateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from app import constants
from django.db import IntegrityError
from django.db.models import Count, Exists, OuterRef
from django.db.utils import IntegrityError
from django.http import FileResponse, HttpResponse, JsonResponse
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django_filters.rest_framework import DjangoFilterBackend
from recipe.models.ingredient import Ingredient
from recipe.models.recipe import Recipe, RecipeIngredient
from recipe.models.recipe_user_model import Cart, Favorite
from recipe.models.tag import Tag
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from users.models import Subscribtion, User


@api_view(["PUT", "DELETE"])
def avatar(request):
    if request.method == "PUT":
        user = request.user

        serializer = AvatarSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(
                {"avatar": user.avatar.url},
                status=HTTPStatus.OK
            )

        return JsonResponse(
            {"field_name": [str(field[0])
                            for field in serializer.errors.values()]},
            status=HTTPStatus.BAD_REQUEST
        )

    elif request.method == "DELETE":
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


@api_view(["POST", "DELETE"])
def shopping_cart(request, recipe_id):
    return handle_user_recipe_relation(
        request, recipe_id,
        serializer_class=CartSerializer,
        already_exists_msg="Рецепт уже в корзине",
        not_in_relation_msg="Рецепт не в корзине"
    )


@api_view(["GET"])
def download_shopping_cart(request):
    cart = Cart.objects.filter(
        user=request.user).values_list("recipe_id", flat=True)
    ingredients = RecipeIngredient.objects.filter(
        recipe_id__in=cart
    ).select_related(
        "ingredient", "recipe"
    )

    cart_ingredients = {}
    for ingredient in ingredients:
        cart_ingredient = cart_ingredients.pop(
            ingredient.id,
            {
                "name": ingredient.ingredient.name,
                "measurement_unit": ingredient.ingredient.measurement_unit,
                "amount": 0,
            },
        )
        cart_ingredient["amount"] += ingredient.amount

        cart_ingredients[ingredient.id] = cart_ingredient

    pdf = gen_pdf(cart_ingredients.values())
    now = timezone.now()
    filename = f'cart-{now.strftime("%d-%m-%Y-%H-%M")}.pdf'

    return FileResponse(pdf, as_attachment=True, filename=filename)


def gen_pdf(ingredients):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    font_path = pathlib.Path("static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "DejaVuSans"

    elements = []
    elements.append(Paragraph("Список ингредиентов:", style))
    elements.append(Spacer(1, 10))

    for i, ingredient in enumerate(ingredients):
        if i == len(ingredients) - 1:
            line = (
                f'- {ingredient["name"]}: {ingredient["amount"]} '
                f'{ingredient["measurement_unit"]}.'
            )
            elements.append(Paragraph(line, style))
        else:
            line = (
                f'- {ingredient["name"]}: {ingredient["amount"]} '
                f'{ingredient["measurement_unit"]};'
            )
            elements.append(Paragraph(line, style))
            elements.append(Spacer(1, 6))

    doc.build(elements)
    buffer.seek(0)

    return buffer


@api_view(["POST", "DELETE"])
def favorite(request, recipe_id):
    return handle_user_recipe_relation(
        request, recipe_id,
        serializer_class=FavoriteSerializer,
        already_exists_msg="Рецепт уже в избранном",
        not_in_relation_msg="Рецепт не в избранном"
    )


class IngredientListView(ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSingleSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = None

    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    ordering_fields = ["name"]
    ordering = ["name"]


@require_GET
def ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.filter(id=ingredient_id).first()
    if not ingredient:
        return JsonResponse(
            {"field_name": ["Ингредиент не найден"]},
            status=HTTPStatus.BAD_REQUEST
        )
    return JsonResponse(IngredientSingleSerializer(ingredient).data)


@csrf_exempt
def short_link(request, link):
    recipe_id = int(link, 16)
    return redirect(f"/recipes/{recipe_id}")


@csrf_exempt
def get_link(request, recipe_id):
    recipe = Recipe.objects.filter(id=recipe_id).first()

    if not recipe:
        return JsonResponse(
            {"detail": "Recipe not found"},
            status=HTTPStatus.NOT_FOUND
        )

    link = hex(recipe.id)
    return JsonResponse(
        {"short-link": request.build_absolute_uri(
            reverse("short_link", args=[link]))},
        status=200,
    )


@require_POST
@csrf_exempt
def login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=HTTPStatus.BAD_REQUEST
        )

    try:
        user = User.objects.get(email=data["email"])
    except User.DoesNotExist:
        return JsonResponse(
            {"error": "User does not exist"},
            status=HTTPStatus.BAD_REQUEST
        )

    try:
        valid = user.check_password(data["password"])

        if not valid:
            raise ValueError
    except ValueError:
        return JsonResponse(
            {"error": "Неверный пароль"},
            status=HTTPStatus.BAD_REQUEST
        )

    token, created = Token.objects.get_or_create(user=user)
    return JsonResponse({"auth_token": token.key}, status=HTTPStatus.OK)


@api_view(["POST"])
def logout(request):
    Token.objects.get(user=request.user).delete()
    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@api_view(["POST"])
def set_password(request):
    user = request.user

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"field_name": ["Invalid JSON"]}, status=HTTPStatus.BAD_REQUEST
        )

    serializer = UserPasswordUpdateSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        return JsonResponse(
            {
                "field_name": [
                    str(field[0]) for field in list(serializer.errors.values())
                ]
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    return HttpResponse(status=HTTPStatus.NO_CONTENT)


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
                    user=user, recipe=OuterRef("pk"))),
                is_in_shopping_cart=Exists(Cart.objects.filter(
                    user=user, recipe=OuterRef("pk")))
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

        paginator = PagePagination()
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
            context={"request": request}
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
                                        recipe=OuterRef("pk"))
                ),
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=request.user, recipe=OuterRef("pk"))
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
                    recipe, context={"request": request}
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


def register_user(request):
    field_errors = []

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"field_name": ["Invalid JSON"]}, status=HTTPStatus.BAD_REQUEST
        )

    serializer = UserSerializer(
        data=request.data, context={"request": request})
    if serializer.is_valid():
        user = serializer.save()
    else:
        field_errors = [str(field[0]) for field in serializer.errors.values()]
        return JsonResponse(
            {"field_name": field_errors},
            status=HTTPStatus.BAD_REQUEST
        )

    try:
        data = {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        return JsonResponse(data, status=HTTPStatus.CREATED)
    except IntegrityError:
        return JsonResponse(
            {"field_name": [
                "Пользователь с таким email или username уже существует"]},
            status=HTTPStatus.BAD_REQUEST,
        )


class SubscribeView(APIView):
    def post(self, request, author_id):
        author = (
            User.objects.filter(id=author_id)
            .annotate(recipes_count=Count("recipes"))
            .first()
        )

        if not author:
            return JsonResponse(
                {"error": "Пользователь не найден"},
                status=HTTPStatus.NOT_FOUND
            )

        if Subscribtion.objects.filter(
            author=author,
            user=request.user
        ).exists():
            return JsonResponse(
                {"error": "Подписка уже существует"},
                status=HTTPStatus.BAD_REQUEST
            )

        if author == request.user:
            return JsonResponse(
                {"error": "Нельзя подписаться на самого себя"},
                status=HTTPStatus.BAD_REQUEST,
            )

        serializer = SubscribtionSerializer(
            data={"author": author.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return JsonResponse(
            UserWithRecipesSerializer(
                author, context={"request": request}).data,
            status=HTTPStatus.CREATED,
        )

    def delete(self, request, author_id):
        author = User.objects.filter(id=author_id).first()

        if not author:
            return JsonResponse(
                {"error": "Пользователь не найден"},
                status=HTTPStatus.NOT_FOUND
            )

        deleted, _ = Subscribtion.objects.filter(
            author=author, user=request.user
        ).delete()

        if not deleted:
            return JsonResponse(
                {"error": "Подписка не найдена"}, status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


@api_view(["GET"])
def subscribtions(request):
    subbed = User.objects.filter(
        id__in=Subscribtion.objects.filter(user=request.user).values_list(
            "author_id", flat=True
        )
    ).annotate(recipes_count=Count("recipes"))

    paginator = PagePagination()
    if request.GET.get("limit"):
        paginator.page_size = request.GET.get("limit")
    result_page = paginator.paginate_queryset(subbed, request)

    serializer = UserWithRecipesSerializer(
        result_page, many=True, context={"request": request}
    )
    return paginator.get_paginated_response(serializer.data)


@require_GET
def tags(request):
    tag_list = TagSerializer(Tag.objects.all(), many=True).data

    return JsonResponse(tag_list, safe=False)


@require_GET
def tag(request, tag_id):
    tag = Tag.objects.filter(id=tag_id).first()
    if not tag:
        return JsonResponse(
            {"detail": "Тег не найден"},
            status=HTTPStatus.NOT_FOUND
        )
    return JsonResponse(TagSerializer(tag).data)


class UserListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        request = auth_user(request)

        paginator = PagePagination()
        paginator.page_size = request.GET.get(
            "limit", constants.PAGINATE_COUNT)
        queryset = User.objects.all()

        result_page = paginator.paginate_queryset(queryset, request)
        serializer = UserSerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        return register_user(request)


class UserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        request = auth_user(request)

        user = User.objects.filter(id=user_id).first()

        if not user:
            return JsonResponse(
                {"detail": "User does not exist"}, status=HTTPStatus.NOT_FOUND
            )

        return JsonResponse(UserSerializer(
            user, context={"request": request}
        ).data)


class MeView(APIView):
    def get(self, request):
        return JsonResponse(
            UserSerializer(request.user, context={"request": request}).data
        )


def auth_user(request):
    auth = TokenAuthentication()
    try:
        user_auth_tuple = auth.authenticate(request)
        if user_auth_tuple:
            request.user, request.auth = user_auth_tuple
    except AuthenticationFailed:
        request.user, request.auth = None, None
    finally:
        return request


def handle_user_recipe_relation(request, recipe_id, serializer_class,
                                already_exists_msg="Рецепт уже добавлен",
                                not_in_relation_msg="Рецепт не в списке"):
    recipe = Recipe.objects.filter(id=recipe_id).first()
    if not recipe:
        return JsonResponse(
            {"error": "Рецепт не найден"},
            status=HTTPStatus.NOT_FOUND
        )

    if request.method == "POST":
        try:
            serializer = serializer_class(
                data={"user": request.user.id, "recipe": recipe_id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except IntegrityError:
            return JsonResponse(
                {"field_name": [already_exists_msg]},
                status=HTTPStatus.BAD_REQUEST
            )
        return JsonResponse(
            ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED
        )

    if request.method == "DELETE":
        deleted, _ = serializer_class.Meta.model.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not deleted:
            return JsonResponse(
                {"error": not_in_relation_msg},
                status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
