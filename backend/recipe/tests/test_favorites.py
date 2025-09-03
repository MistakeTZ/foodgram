import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from recipe.models.recipe import Recipe
from recipe.models.favorite import Favorite
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
    return Recipe.objects.create(
        title="Суп", author=user, cooking_time=10
    )


@pytest.mark.django_db
class TestFavorite:
    def test_add_recipe_to_favorites(self, auth_client, recipe, user):
        url = reverse("favorite", args=[recipe.id])
        response = auth_client.post(url)

        assert response.status_code == 201
        assert Favorite.objects.filter(user=user, recipe=recipe).exists()

    def test_add_recipe_already_in_favorites(self, auth_client, recipe, user):
        Favorite.objects.create(user=user, recipe=recipe)
        url = reverse("favorite", args=[recipe.id])
        response = auth_client.post(url)

        assert response.status_code == 400
        assert response.json()["error"] == "Рецепт уже в избранном"

    def test_add_nonexistent_recipe(self, auth_client):
        url = reverse("favorite", args=[999])
        response = auth_client.post(url)

        assert response.status_code == 404
        assert response.json()["error"] == "Рецепт не найден"

    def test_delete_recipe_from_favorites(self, auth_client, recipe, user):
        Favorite.objects.create(user=user, recipe=recipe)
        url = reverse("favorite", args=[recipe.id])
        response = auth_client.delete(url)

        assert response.status_code == 204
        assert not Favorite.objects.filter(user=user, recipe=recipe).exists()

    def test_delete_recipe_not_in_favorites(self, auth_client, recipe):
        url = reverse("favorite", args=[recipe.id])
        response = auth_client.delete(url)

        assert response.status_code == 400
        assert response.json()["error"] == "Рецепт не в избранном"
