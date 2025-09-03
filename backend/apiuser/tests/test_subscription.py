import pytest
import json
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from apiuser.models import Subscribtion


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="user1", email="u1@example.com", password="Test1234")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="user2", email="u2@example.com", password="Test1234")


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.mark.django_db
class TestSubscribe:
    def test_subscribe_success(self, auth_client, user, other_user):
        url = reverse("subscribe", args=[other_user.id])
        response = auth_client.post(url)
        assert response.status_code == 201
        assert Subscribtion.objects.filter(
            user=user, author=other_user).exists()

    def test_subscribe_self(self, auth_client, user):
        url = reverse("subscribe", args=[user.id])
        response = auth_client.post(url)
        assert response.status_code == 400
        assert response.json()["error"] == "Нельзя подписаться на самого себя"

    def test_subscribe_already_exists(self, auth_client, user, other_user):
        Subscribtion.objects.create(user=user, author=other_user)
        url = reverse("subscribe", args=[other_user.id])
        response = auth_client.post(url)
        assert response.status_code == 400
        assert response.json()["error"] == "Подписка уже существует"

    def test_subscribe_user_not_found(self, auth_client):
        url = reverse("subscribe", args=[9999])
        response = auth_client.post(url)
        assert response.status_code == 404
        assert response.json()["error"] == "Польлзователь не найден"

    def test_unsubscribe_success(self, auth_client, user, other_user):
        Subscribtion.objects.create(user=user, author=other_user)
        url = reverse("subscribe", args=[other_user.id])
        response = auth_client.delete(url)
        assert response.status_code == 204
        assert not Subscribtion.objects.filter(
            user=user, author=other_user).exists()

    def test_unsubscribe_not_found(self, auth_client, user, other_user):
        url = reverse("subscribe", args=[other_user.id])
        response = auth_client.delete(url)
        assert response.status_code == 400
        assert response.json()["error"] == "Подписка не найдена"

    def test_subscribe_no_auth(self, api_client, other_user):
        url = reverse("subscribe", args=[other_user.id])
        response = api_client.post(url)
        assert response.status_code == 401

    def test_unsubscribe_no_auth(self, api_client, other_user):
        url = reverse("subscribe", args=[other_user.id])
        response = api_client.delete(url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestSubscribtionsList:
    def test_subscribtions_list(self, auth_client, user, other_user):
        # создаём несколько подписок
        for i in range(12):
            u = User.objects.create_user(
                username=f"user{i + 10}", email=f"u{i + 10}@ex.com", password="Test1234")
            Subscribtion.objects.create(user=user, author=u)

        url = reverse("subscribtions")
        response = auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        # пагинация 10 на страницу
        assert data["count"] >= 12
        assert len(data["results"]) == 10

    def test_subscribtions_no_auth(self, api_client):
        url = reverse("subscribtions")
        response = api_client.get(url)
        assert response.status_code == 401
