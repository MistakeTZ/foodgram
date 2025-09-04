import pytest
import json
from PIL import Image
from io import BytesIO
import base64
from django.urls import reverse
from django.core.files.base import ContentFile
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from recipe.models.recipe import Recipe, Ingredient, RecipeIngredient, Tag
from recipe.models.cart import Cart
from recipe.models.favorite import Favorite
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="user1", password="pass123")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="user2", password="pass123")


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def ingredient(db):
    return Ingredient.objects.create(name="Соль", measurement_unit="г")


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="Обед", slug="lunch")


@pytest.fixture
def recipe(db, user, ingredient, tag):
    # Создаём маленькое изображение 1x1 px
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    # Создаём ContentFile для Django
    image_file = ContentFile(img_bytes, name="test.png")

    # Создаём рецепт с изображением
    r = Recipe.objects.create(
        title="Суп",
        author=user,
        cooking_time=10,
        image=image_file
    )
    r.tags.add(tag)
    RecipeIngredient.objects.create(recipe=r, ingredient=ingredient, amount=2)
    return r


@pytest.mark.django_db
class TestRecipesViewFull:
    def test_get_recipes_list(self, api_client, recipe):
        url = reverse("recipes")
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert any(r["id"] == recipe.id for r in data["results"])

    def test_create_recipe_success(self, auth_client, ingredient, tag):
        url = reverse("recipes")
        # простое base64 изображение 1x1 png
        img_data = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00").decode()
        payload = {
            "name": "Новый рецепт",
            "text": "Описание",
            "cooking_time": 15,
            "image": f"data:image/png;base64,{img_data}",
            "ingredients": [{"id": ingredient.id, "amount": 3}],
            "tags": [tag.id]
        }
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        # После редиректа Django возвращает код 302
        assert response.status_code == 302
        # Проверяем, что рецепт создался
        from recipe.models.recipe import Recipe
        r = Recipe.objects.get(title="Новый рецепт")
        assert r.cooking_time == 15
        assert r.tags.first() == tag
        ing = RecipeIngredient.objects.get(recipe=r, ingredient=ingredient)
        assert ing.amount == 3

    def test_create_recipe_missing_fields(self, auth_client):
        url = reverse("recipes")
        payload = {"name": "Test"}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert "Поле ingredients отсутствует" in response.json()["field_name"]

    def test_create_recipe_invalid_token(self, api_client):
        url = reverse("recipes")
        payload = {"name": "Test", "text": "Desc", "cooking_time": 10,
                   "image": None, "ingredients": [], "tags": []}
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 401

    def test_get_recipes_filtered_by_author(self, auth_client, recipe, user):
        url = reverse("recipes") + f"?author={user.id}"
        response = auth_client.get(url)
        data = response.json()
        assert response.status_code == 200
        assert any(r["id"] == recipe.id for r in data["results"])

    def test_get_recipes_is_favorited(self, auth_client, recipe, user):
        Favorite.objects.create(user=user, recipe=recipe)
        url = reverse("recipes") + "?is_favorited=1"
        response = auth_client.get(url)
        data = response.json()
        assert response.status_code == 200
        assert any(r["id"] == recipe.id for r in data["results"])

    def test_get_recipes_is_in_cart(self, auth_client, recipe, user):
        Cart.objects.create(user=user, recipe=recipe)
        url = reverse("recipes") + "?is_in_shopping_cart=1"
        response = auth_client.get(url)
        data = response.json()
        assert response.status_code == 200
        assert any(r["id"] == recipe.id for r in data["results"])


@pytest.mark.django_db
class TestRecipeViewFull:
    def test_get_recipe(self, api_client, recipe):
        url = reverse("recipe", args=[recipe.id])
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == recipe.id

    def test_patch_recipe_success(self, auth_client, recipe, ingredient, tag):
        url = reverse("recipe", args=[recipe.id])
        img_data = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00").decode()
        payload = {
            "name": "Обновлено",
            "text": "Текст обновлён",
            "cooking_time": 5,
            "image": f"data:image/png;base64,{img_data}",
            "ingredients": [{"id": ingredient.id, "amount": 10}],
            "tags": [tag.id]
        }
        response = auth_client.patch(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 200
        recipe.refresh_from_db()
        assert recipe.title == "Обновлено"
        ing = RecipeIngredient.objects.get(
            recipe=recipe, ingredient=ingredient)
        assert ing.amount == 10

    def test_patch_recipe_no_auth(self, api_client, recipe):
        url = reverse("recipe", args=[recipe.id])
        payload = {"name": "Обновлено", "text": "Текст",
                   "cooking_time": 5, "image": None,
                   "ingredients": [], "tags": []}
        response = api_client.patch(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 401

    def test_patch_recipe_not_author(self, auth_client, recipe, other_user):
        token, _ = Token.objects.get_or_create(user=other_user)
        auth_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        url = reverse("recipe", args=[recipe.id])
        payload = {"name": "Обновлено", "text": "Текст",
                   "cooking_time": 5, "image": None,
                   "ingredients": [], "tags": []}
        response = auth_client.patch(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 403

    def test_delete_recipe_success(self, auth_client, recipe):
        url = reverse("recipe", args=[recipe.id])
        response = auth_client.delete(url)
        assert response.status_code == 204
        from recipe.models.recipe import Recipe
        assert not Recipe.objects.filter(id=recipe.id).exists()

    def test_delete_recipe_no_auth(self, api_client, recipe):
        url = reverse("recipe", args=[recipe.id])
        response = api_client.delete(url)
        assert response.status_code == 401

    def test_delete_recipe_not_author(self, auth_client, recipe, other_user):
        token, _ = Token.objects.get_or_create(user=other_user)
        auth_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        url = reverse("recipe", args=[recipe.id])
        response = auth_client.delete(url)
        assert response.status_code == 403
