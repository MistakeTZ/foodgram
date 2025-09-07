import io
from datetime import datetime, timedelta, timezone
from os import path

from recipe.models.recipe import Recipe, RecipeIngredient
from recipe.models.recipe_user_model import Cart
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from rest_framework.decorators import api_view
from api.serializers.user_recipe_serializer import CartSerializer
from api.views.user_reciepe_relation import handle_user_recipe_relation
from django.http import FileResponse


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

    pdf = gen_pdf(cart_ingredients.values())
    now = datetime.now(tz=timezone(timedelta(hours=3)))
    filename = f"cart-{now.strftime('%d-%m-%Y-%H-%M')}.pdf"

    return FileResponse(pdf, as_attachment=True, filename=filename)


def gen_pdf(ingredients):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    font_path = path.join("static", "fonts", "DejaVuSans.ttf")
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
