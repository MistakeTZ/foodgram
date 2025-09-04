import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from recipe.models.recipe import Recipe, Ingredient, RecipeIngredient
from recipe.models.cart import Cart
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="test", password="pass123")


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def recipe(db, user):
    return Recipe.objects.create(title="Soup", author=user, cooking_time=10)


@pytest.mark.django_db
class TestShoppingCart:
    def test_add_recipe_to_cart(self, auth_client, recipe, user):
        url = reverse("shopping_cart", args=[recipe.id])
        response = auth_client.post(url)
        assert response.status_code == 201
        assert Cart.objects.filter(user=user, recipe=recipe).exists()

    def test_add_recipe_already_in_cart(self, auth_client, recipe, user):
        Cart.objects.create(user=user, recipe=recipe)
        url = reverse("shopping_cart", args=[recipe.id])
        response = auth_client.post(url)
        assert response.status_code == 400
        assert response.json()["error"] == "Рецепт уже в избранном"

    def test_delete_recipe_from_cart(self, auth_client, recipe, user):
        Cart.objects.create(user=user, recipe=recipe)
        url = reverse("shopping_cart", args=[recipe.id])
        response = auth_client.delete(url)
        assert response.status_code == 204
        assert not Cart.objects.filter(user=user, recipe=recipe).exists()

    def test_delete_not_in_cart(self, auth_client, recipe):
        url = reverse("shopping_cart", args=[recipe.id])
        response = auth_client.delete(url)
        assert response.status_code == 400
        assert response.json()["error"] == "Рецепт не в избранном"


@pytest.mark.django_db
class TestDownloadShoppingCart:
    def test_download_cart_pdf(self, auth_client, recipe, user):
        # создаём ингредиент и добавляем в рецепт
        ingredient = Ingredient.objects.create(
            name="Potato", measurement_unit="kg"
        )
        RecipeIngredient.objects.create(
            recipe=recipe, ingredient=ingredient, amount=2
        )
        Cart.objects.create(user=user, recipe=recipe)

        url = reverse("download_shopping_cart")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        content = b"".join(response.streaming_content)
        assert content.startswith(b"%PDF")  # файл действительно PDF
