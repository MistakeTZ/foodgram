import io
import pathlib
from http import HTTPStatus

from django.db import IntegrityError
from django.db.models import Count, Exists, OuterRef
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from recipe.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import (
    AuthenticationFailed,
    PermissionDenied,
    ParseError,
)
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (
    ModelViewSet,
    ReadOnlyModelViewSet,
    ViewSet,
)

from api.filters import IngredientFilter, RecipeFilter
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
    UserSerializer,
    UserWithRecipesSerializer,
    UserWriteSerializer,
)
from users.models import Subscribtion, User


class ShoppingCartViewSet(ViewSet):
    """ViewSet для работы с корзиной."""

    @action(detail=True, methods=["post", "delete"])
    def recipes(self, request, pk=None):
        return handle_user_recipe_relation(
            request,
            pk,
            serializer_class=CartSerializer,
            already_exists_msg="Рецепт уже в корзине",
            not_in_relation_msg="Рецепт не в корзине",
        )

    @action(detail=False, methods=["get"])
    def download(self, request):
        cart = Cart.objects.filter(user=request.user).values_list(
            "recipe_id", flat=True,
        )

        ingredients = RecipeIngredient.objects.filter(
            recipe_id__in=cart,
        ).select_related("ingredient", "recipe")

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

        pdf = self.gen_pdf(cart_ingredients.values())
        now = timezone.now()
        filename = f'cart-{now.strftime("%d-%m-%Y-%H-%M")}.pdf'

        return FileResponse(pdf, as_attachment=True, filename=filename)

    def gen_pdf(self, ingredients):
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


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet для ингредиентов. Поддерживает list и retrieve."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSingleSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = None

    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    ordering_fields = ["name"]
    ordering = ["name"]


class ShortLinkViewSet(ViewSet):
    """ViewSet для генерации и перехода по коротким ссылкам рецептов."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @action(detail=True, methods=["get"])
    def get_link(self, request, recipe_id=None):
        recipe = Recipe.objects.filter(id=recipe_id).exists()
        if not recipe:
            return JsonResponse(
                {"detail": "Recipe not found"}, status=HTTPStatus.NOT_FOUND,
            )

        link = hex(recipe_id)
        short_url = request.build_absolute_uri(
            reverse("short-link", args=[link]),
        )
        return JsonResponse(
            {"short-link": short_url},
            status=200,
        )

    @action(detail=True, methods=["get"])
    def short_link(self, request, link=None):
        recipe_id = int(link, 16)
        return redirect(f"/recipes/{recipe_id}")


class RecipeViewSet(ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    serializer_class = RecipeSerializer
    pagination_class = PagePagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RecipeFilter
    ordering_fields = ["id", "name", "cooking_time"]
    ordering = ["-created"]

    def get_queryset(self):
        user = self.request.user

        qs = Recipe.objects.select_related("author").prefetch_related(
            "tags", "ingredients", "recipe_ingredients__ingredient",
        )

        if user.is_authenticated:
            qs = qs.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef("pk")),
                ),
                is_in_shopping_cart=Exists(
                    Cart.objects.filter(user=user, recipe=OuterRef("pk")),
                ),
            )
        else:
            qs = qs.annotate(
                is_favorited=Exists(Favorite.objects.none()),
                is_in_shopping_cart=Exists(Cart.objects.none()),
            )

        return qs

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise AuthenticationFailed("No permission")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)

        read_serializer = RecipeSerializer(
            recipe,
            context={"request": request},
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=HTTPStatus.CREATED, headers=headers,
        )

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise AuthenticationFailed("No permission")

        partial = kwargs.pop("partial", False)
        if partial:
            field_names = [
                field
                for field in [
                    "name",
                    "text",
                    "cooking_time",
                    "ingredients",
                    "tags",
                ]
                if field not in request.data
            ]
            if field_names:
                raise ParseError({"field_name": field_names})

        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        read_serializer = RecipeSerializer(
            recipe,
            context={"request": request},
        )
        return Response(read_serializer.data)

    def perform_update(self, serializer):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed("No permission")

        recipe = self.get_object()
        if recipe.author != self.request.user:
            raise PermissionDenied("No permission")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed("No permission")

        if instance.author != self.request.user:
            raise PermissionDenied("No permission")
        instance.delete()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]
    serializer_class = UserSerializer
    pagination_class = PagePagination

    def get_subscriptions_queryset(self):
        return User.objects.filter(
            id__in=Subscribtion.objects.filter(
                user=self.request.user,
            ).values_list(
                "author_id", flat=True,
            ),
        ).annotate(recipes_count=Count("recipes"))

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context={"request": request},
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        author = (
            User.objects.filter(id=pk).annotate(
                recipes_count=Count("recipes"),
            ).first()
        )
        if not author:
            return Response(
                {"error": "Пользователь не найден"},
                status=HTTPStatus.NOT_FOUND,
            )

        if request.method == "DELETE":
            deleted, _ = Subscribtion.objects.filter(
                user=request.user, author=author,
            ).delete()
            if not deleted:
                return Response(
                    {"error": "Подписка не найдена"},
                    status=HTTPStatus.BAD_REQUEST,
                )
            return Response(status=HTTPStatus.NO_CONTENT)

        if author == request.user:
            return Response(
                {"error": "Нельзя подписаться на самого себя"},
                status=HTTPStatus.BAD_REQUEST,
            )

        if Subscribtion.objects.filter(
            user=request.user,
            author=author,
        ).exists():
            return Response(
                {"error": "Подписка уже существует"},
                status=HTTPStatus.BAD_REQUEST,
            )

        serializer = SubscribtionSerializer(
            data={"author": author.id}, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(
            UserWithRecipesSerializer(
                author, context={"request": request},
            ).data,
            status=HTTPStatus.CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        qs = self.get_subscriptions_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={"request": request},
        )
        return paginator.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = UserWriteSerializer(
            data=request.data, context={"request": request},
        )
        if serializer.is_valid():
            try:
                user = serializer.save()
            except IntegrityError:
                return Response(
                    {
                        "field_name": [
                            (
                                "Пользователь с таким email "
                                "или username уже существует",
                            ),
                        ],
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
            data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
            return Response(data, status=HTTPStatus.CREATED)
        else:
            field_errors = [
                str(field[0]) for field in serializer.errors.values()
            ]
            return Response(
                {"field_name": field_errors},
                status=HTTPStatus.BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"avatar": user.avatar.url},
                    status=HTTPStatus.OK,
                )
            field_errors = [
                str(field[0]) for field in serializer.errors.values()
            ]
            return Response(
                {"field_name": field_errors},
                status=HTTPStatus.BAD_REQUEST,
            )

        elif request.method == "DELETE":
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [AllowAny]
    authentication_classes = []


def handle_user_recipe_relation(
    request,
    recipe_id,
    serializer_class,
    already_exists_msg="Рецепт уже добавлен",
    not_in_relation_msg="Рецепт не в списке",
):
    recipe = Recipe.objects.filter(id=recipe_id).first()
    if not recipe:
        return JsonResponse(
            {"error": "Рецепт не найден"},
            status=HTTPStatus.NOT_FOUND,
        )

    if request.method == "POST":
        try:
            serializer = serializer_class(
                data={"user": request.user.id, "recipe": recipe_id},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except IntegrityError:
            return JsonResponse(
                {"field_name": [already_exists_msg]},
                status=HTTPStatus.BAD_REQUEST,
            )
        return JsonResponse(
            ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )

    if request.method == "DELETE":
        deleted, _ = serializer_class.Meta.model.objects.filter(
            user=request.user, recipe=recipe,
        ).delete()
        if not deleted:
            return JsonResponse(
                {"error": not_in_relation_msg}, status=HTTPStatus.BAD_REQUEST,
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


@api_view(["POST", "DELETE"])
def favorite(request, recipe_id):
    return handle_user_recipe_relation(
        request,
        recipe_id,
        serializer_class=FavoriteSerializer,
        already_exists_msg="Рецепт уже в избранном",
        not_in_relation_msg="Рецепт не в избранном",
    )
