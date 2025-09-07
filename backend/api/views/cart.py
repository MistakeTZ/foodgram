import io
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from os import path

from api.serializers.short_recipe import ShortRecipeSerializer
from django.db.utils import IntegrityError
from django.http import FileResponse, HttpResponse, JsonResponse
from recipe.models.recipe import Recipe, RecipeIngredient
from recipe.models.recipe_user_model import Cart
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from rest_framework.decorators import api_view


# Изменение списка покупок
@api_view(["POST", "DELETE"])
def shopping_cart(request, recipe_id):
    recipe = Recipe.objects.filter(id=recipe_id).first()

    # Проверка существования рецепта
    if not recipe:
        return JsonResponse(
            {"error": "Рецепт не найден"},
            status=HTTPStatus.NOT_FOUND
        )

    # Добавление рецепта в список
    if request.method == "POST":
        try:
            Cart.objects.create(user=request.user, recipe=recipe)
        except IntegrityError:
            return JsonResponse(
                {"field_name": ["Рецепт уже в избранном"]},
                status=HTTPStatus.BAD_REQUEST,
            )
        return JsonResponse(
            ShortRecipeSerializer(recipe).data, status=HTTPStatus.CREATED
        )

    # Удаление рецепта из списка
    if request.method == "DELETE":
        is_deleted = Cart.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not is_deleted[0]:
            return JsonResponse(
                {"error": "Рецепт не в избранном"},
                status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


# Скачивание списка покупок
@api_view(["GET"])
def download_shopping_cart(request):
    # Получение списка ингредиентов
    cart = Cart.objects.filter(
        user=request.user).values_list("recipe_id", flat=True)
    # TODO: Создавать объект нужно через сохранение сериалайзера,
    # а не подобным образом вручную
    ingredients = RecipeIngredient.objects.filter(
        recipe_id__in=cart
    ).select_related(
        "ingredient", "recipe"
    )

    # Группировка ингредиентов
    cart_ingredients = {}
    for ingredient in ingredients:
        ingredient = cart_ingredients.pop(
            ingredient.id,
            {
                "name": ingredient.ingredient.name,
                "measurement_unit": ingredient.ingredient.measurement_unit,
                "amount": 0,
            },
        )
        ingredient["amount"] += ingredient.amount

        cart_ingredients[ingredient.id] = ingredient

    # Генерация PDF
    pdf = gen_pdf(cart_ingredients.values())
    now = datetime.now(tz=timezone(timedelta(hours=3)))
    filename = f"cart-{now.strftime('%d-%m-%Y-%H-%M')}.pdf"

    return FileResponse(pdf, as_attachment=True, filename=filename)


# Генерация PDF
def gen_pdf(ingredients):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    # Регистрация шрифта
    font_path = path.join("static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    # Создание документа
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "DejaVuSans"

    elements = []
    elements.append(Paragraph("Список ингредиентов:", style))
    elements.append(Spacer(1, 10))

    # Добавление ингредиентов
    for i, ingredient in enumerate(ingredients):
        if i == len(ingredients) - 1:
            line = (
                f"- {ingredient['name']}: {ingredient['amount']} "
                f"{ingredient['measurement_unit']}."
            )
            elements.append(Paragraph(line, style))
        else:
            line = (
                f"- {ingredient['name']}: {ingredient['amount']} "
                f"{ingredient['measurement_unit']};"
            )
            elements.append(Paragraph(line, style))
            elements.append(Spacer(1, 6))

    doc.build(elements)
    buffer.seek(0)

    return buffer
