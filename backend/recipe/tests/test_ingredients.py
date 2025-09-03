import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from recipe.models.ingredient import Ingredient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def ingredients(db):
    return [
        Ingredient.objects.create(name="Соль", measurement_unit="г"),
        Ingredient.objects.create(name="Сахар", measurement_unit="г"),
        Ingredient.objects.create(name="Масло", measurement_unit="мл"),
    ]


@pytest.mark.django_db
class TestIngredients:
    def test_list_all_ingredients(self, api_client, ingredients):
        url = reverse("ingredients")
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert any(ing["name"] == "Соль" for ing in data)

    def test_filter_ingredients_by_name(self, api_client, ingredients):
        url = reverse("ingredients") + "?name=Са"
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert all("Са" in ing["name"] for ing in data)
        assert data[0]["name"] == "Сахар"  # начинается с "Са" → идёт первым

    def test_get_single_ingredient(self, api_client, ingredients):
        ingredient = ingredients[0]
        url = reverse("ingredient", args=[ingredient.id])
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ingredient.id
        assert data["name"] == ingredient.name
        assert data["measurement_unit"] == ingredient.measurement_unit

    def test_get_single_ingredient_not_found(self, api_client):
        url = reverse("ingredient", args=[999])
        response = api_client.get(url)

        assert response.status_code == 400
        data = response.json()
        assert "Ингредиент не найден" in data["field_name"]
