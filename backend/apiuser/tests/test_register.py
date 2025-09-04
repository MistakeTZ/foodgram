import pytest
import json
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
import unicodedata


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestRegisterUser:
    def test_register_success(self, api_client):
        url = reverse("users")
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "First",
            "last_name": "Last",
            "password": "Password1"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    def test_register_invalid_json(self, api_client):
        url = reverse("users")
        response = api_client.post(
            url, data="not json", content_type="application/json")
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["field_name"]

    def test_register_invalid_email(self, api_client):
        url = reverse("users")
        payload = {
            "email": "invalid-email",
            "username": "testuser",
            "first_name": "First",
            "last_name": "Last",
            "password": "Password1"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert "Некорректный email" in response.json()["field_name"]

    def test_register_invalid_username(self, api_client):
        url = reverse("users")
        payload = {
            "email": "test@example.com",
            "username": "user!@#",
            "first_name": "First",
            "last_name": "Last",
            "password": "Password1"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert "Некорректный username" in response.json()["field_name"]

    def test_register_short_password(self, api_client):
        url = reverse("users")
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "First",
            "last_name": "Last",
            "password": "Pass1"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Пароль слишком короткий") in norm(
            response.json()["field_name"][0])

    def test_register_no_letter_password(self, api_client):
        url = reverse("users")
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "First",
            "last_name": "Last",
            "password": "12345678"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert "Пароль должен содержать букву" in response.json()[
            "field_name"][0]

    def test_register_no_number_password(self, api_client):
        url = reverse("users")
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "First",
            "last_name": "Last",
            "password": "Password"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert "Пароль должен содержать цифру" in response.json()[
            "field_name"][0]

    def test_users_already_exists(self, api_client):
        User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="Password1"
        )
        url = reverse("users")
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "First",
            "last_name": "Last",
            "password": "Password1"
        }
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Пользователь с таким email или username уже существует"
                    ) in norm(response.json()["field_name"][0])
