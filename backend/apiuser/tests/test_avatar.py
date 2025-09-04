import pytest
import json
import base64
from io import BytesIO
from PIL import Image
from django.urls import reverse
from django.core.files.base import ContentFile
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apiuser.models import Profile
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    u = User.objects.create_user(username="testuser", password="pass123")
    Profile.objects.get_or_create(user=u)
    return u


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.mark.django_db
class TestAvatar:
    def test_put_avatar_success(self, auth_client, user):
        # создаём маленькое изображение 1x1 px
        img = Image.new("RGB", (1, 1), color=(255, 0, 0))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        img_data = f"data:image/png;base64,{img_base64}"

        url = reverse("avatar")
        payload = {"avatar": img_data}

        response = auth_client.put(url, data=json.dumps(
            payload), content_type="application/json")
        assert response.status_code == 200
        data = response.json()
        profile = Profile.objects.get(user=user)
        assert profile.avatar
        assert data["avatar"] == profile.avatar.url

    def test_put_avatar_invalid_json(self, auth_client):
        url = reverse("avatar")
        response = auth_client.put(
            url, data="not json", content_type="application/json")
        assert response.status_code == 400
        assert response.json()["field_name"] == ["Invalid JSON"]

    def test_put_avatar_no_auth(self, api_client):
        url = reverse("avatar")
        response = api_client.put(url, data=json.dumps(
            {"avatar": "data"}), content_type="application/json")
        assert response.status_code == 401

    def test_delete_avatar_success(self, auth_client, user):
        profile = Profile.objects.get(user=user)
        # задаём тестовое изображение
        profile.avatar.save("test.png", ContentFile(b"123"), save=True)
        assert profile.avatar

        url = reverse("avatar")
        response = auth_client.delete(url)
        assert response.status_code == 204

        profile.refresh_from_db()
        assert not profile.avatar

    def test_delete_avatar_no_auth(self, api_client):
        url = reverse("avatar")
        response = api_client.delete(url)
        assert response.status_code == 401
