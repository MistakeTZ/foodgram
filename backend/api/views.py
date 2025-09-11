import io
import pathlib
from http import HTTPStatus

from django.db import IntegrityError
from django.db.models import Count, Exists, OuterRef
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
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
from recipe.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from users.models import Subscribtion, User


class ShoppingCartViewSet(ViewSet):
    """ViewSet для работы с корзиной."""

    @action(detail=True, methods=["post", "delete"])
    def recipes(self, request, pk=None):
        return handle_user_recipe_relation(
            request,
            pk,
            CartSerializer,
            Cart,
            "Рецепт уже в корзине",
            "Рецепт не в корзине",
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
        get_object_or_404(Recipe, id=recipe_id)

        link = hex(recipe_id)
        short_url = request.build_absolute_uri(
            reverse("short-link", args=[link]),
        )
        return JsonResponse(
            {"short-link": short_url},
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

    def get_permissions(self):
        """Определение прав доступа в зависимости от действия."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ["create", "update", "partial_update"]:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def create(self, request, *args, **kwargs):
        """Создание рецепта с возвратом read-serializer данных."""
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)

        recipe = write_serializer.save()

        # Возвращаем данные через read-serializer
        read_serializer = RecipeSerializer(
            recipe,
            context={"request": request},
        )

        headers = self.get_success_headers(write_serializer.data)
        return Response(
            read_serializer.data,
            status=HTTPStatus.CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        """Обновление рецепта с возвратом read-serializer данных."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        write_serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        write_serializer.is_valid(raise_exception=True)

        recipe = write_serializer.save()

        # Возвращаем данные через read-serializer
        read_serializer = RecipeSerializer(
            recipe,
            context={"request": request},
        )

        return Response(read_serializer.data)

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт из избранного."""
        return handle_user_recipe_relation(
            request,
            pk,
            FavoriteSerializer,
            Favorite,
            "Рецепт уже в избранном",
            "Рецепт не в избранном",
        )


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]
    pagination_class = PagePagination
    serializer_class = UserSerializer

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""

        if self.action == "create":
            return UserWriteSerializer
        if self.action in ["subscribe", "subscriptions"]:
            return UserWithRecipesSerializer
        if self.action == "avatar":
            return AvatarSerializer
        return self.serializer_class

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
        author = get_object_or_404(
            User.objects.annotate(
                recipes_count=Count("recipes"),
            ),
            id=pk,
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

        serializer = SubscribtionSerializer(
            data={"author": author.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(self.get_serializer(
            author, context={"request": request},
        ).data, status=HTTPStatus.CREATED)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        qs = self.get_subscriptions_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        serializer = self.get_serializer(
            page, many=True, context={"request": request},
        )
        return paginator.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request},
        )
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                status=HTTPStatus.CREATED,
            )
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
    model_class,
    already_exists_msg="Рецепт уже добавлен",
    not_in_relation_msg="Рецепт не в списке",
):
    recipe = get_object_or_404(Recipe, id=recipe_id)

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
        deleted, _ = model_class.objects.filter(
            user=request.user, recipe=recipe,
        ).delete()
        if not deleted:
            return JsonResponse(
                {"error": not_in_relation_msg}, status=HTTPStatus.BAD_REQUEST,
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
