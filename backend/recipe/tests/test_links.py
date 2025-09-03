import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from recipe.models.recipe import Recipe
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass123")


@pytest.fixture
def recipe(db, user):
    return Recipe.objects.create(
        title="Пюре", author=user, cooking_time=15
    )


@pytest.mark.django_db
class TestShortLink:
    def test_get_short_link_for_recipe(self, api_client, recipe):
        url = reverse("get_link", args=[recipe.id])
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "short-link" in data
        assert hex(recipe.id) in data["short-link"]

    def test_get_short_link_recipe_not_found(self, api_client):
        url = reverse("get_link", args=[999])
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.json()["detail"] == "Recipe not found"

    def test_short_link_redirects(self, api_client, recipe):
        # генерим hex из id рецепта
        short = hex(recipe.id)
        url = reverse("short_link", args=[short])
        response = api_client.get(url)

        assert response.status_code == 302
        assert response.url == f"/recipes/{recipe.id}"
