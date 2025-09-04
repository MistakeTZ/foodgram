import pytest
import json
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import unicodedata


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="testuser", email="test@example.com", password="Test1234")
    return u


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.mark.django_db
class TestAuth:
    # --------------------- LOGIN ---------------------
    def test_login_success(self, api_client, user):
        url = reverse("login")
        payload = {"email": user.email, "password": "Test1234"}
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 200
        assert "auth_token" in response.json()

    def test_login_wrong_email(self, api_client):
        url = reverse("login")
        payload = {"email": "wrong@example.com", "password": "Test1234"}
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert response.json()["error"] == "User does not exist"

    def test_login_wrong_password(self, api_client, user):
        url = reverse("login")
        payload = {"email": user.email, "password": "wrongpass"}
        response = api_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert response.json()["error"] == "Invalid password"

    def test_login_invalid_json(self, api_client):
        url = reverse("login")
        response = api_client.post(
            url, data="not json", content_type="application/json")
        assert response.status_code == 400
        assert response.json()["error"] == "Invalid JSON"

    # --------------------- LOGOUT ---------------------
    def test_logout_success(self, auth_client):
        url = reverse("logout")
        response = auth_client.post(url)
        assert response.status_code == 204

    def test_logout_no_auth(self, api_client):
        url = reverse("logout")
        response = api_client.post(url)
        assert response.status_code == 401

    # --------------------- SET PASSWORD ---------------------
    def test_set_password_success(self, auth_client, user):
        url = reverse("set_password")
        payload = {"current_password": "Test1234",
                   "new_password": "Newpass123"}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 204
        user.refresh_from_db()
        assert user.check_password("Newpass123")

    def test_set_password_wrong_current(self, auth_client):
        url = reverse("set_password")
        payload = {"current_password": "wrong", "new_password": "Newpass123"}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Неверный пароль") in norm(
            response.json()["field_name"][0])

    def test_set_password_invalid_json(self, auth_client):
        url = reverse("set_password")
        response = auth_client.post(
            url, data="not json", content_type="application/json")
        assert response.status_code == 400
        assert norm("Текущий пароль") in [
            norm(resp) for resp in response.json()["field_name"]]
        assert norm("Новый пароль") in [
            norm(resp) for resp in response.json()["field_name"]]

    def test_set_password_too_short(self, auth_client):
        url = reverse("set_password")
        payload = {"current_password": "Test1234", "new_password": "short1"}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Пароль слишком короткий") in norm(
            response.json()["field_name"][0])

    def test_set_password_no_number(self, auth_client):
        url = reverse("set_password")
        payload = {"current_password": "Test1234",
                   "new_password": "NoNumberPass"}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Пароль должен содержать хотя бы одну цифру"
                    ) in norm(response.json()["field_name"][0])

    def test_set_password_no_letter(self, auth_client):
        url = reverse("set_password")
        payload = {"current_password": "Test1234", "new_password": "12345678"}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Пароль должен содержать хотя бы одну букву"
                    ) in norm(response.json()["field_name"][0])

    def test_set_password_too_long(self, auth_client):
        url = reverse("set_password")
        long_pass = "A1" * 100  # >128 chars
        payload = {"current_password": "Test1234", "new_password": long_pass}
        response = auth_client.post(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 400
        assert norm("Пароль слишком длинный") in norm(
            response.json()["field_name"][0])
