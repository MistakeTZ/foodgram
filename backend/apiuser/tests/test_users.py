import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apiuser.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="user1", email="u1@example.com", password="Test1234")


@pytest.fixture
def other_users(db):
    users = []
    for i in range(15):
        users.append(User.objects.create_user(
            username=f"user{i + 2}", email=f"user{i + 2}@ex.com", password="Test1234"))
    return users


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.mark.django_db
class TestUserViews:
    def test_user_list_pagination(self, api_client, user, other_users):
        url = reverse("users")
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        # Всего 16 пользователей (user + 15 других)
        assert data["count"] == 16
        # На первой странице 10 пользователей
        assert len(data["results"]) == 10

    def test_get_user_success(self, api_client, user):
        url = reverse("user", args=[user.id])
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == user.username

    def test_get_user_not_found(self, api_client):
        url = reverse("user", args=[9999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json()["detail"] == "User does not exist"

    def test_me_success(self, auth_client, user):
        url = reverse("me")
        response = auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == user.username

    def test_me_no_auth(self, api_client):
        url = reverse("me")
        response = api_client.get(url)
        assert response.status_code == 401
