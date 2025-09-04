import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from recipe.models.tag import Tag


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tags(db):
    return [
        Tag.objects.create(name="Завтрак", slug="breakfast"),
        Tag.objects.create(name="Обед", slug="lunch"),
    ]


@pytest.mark.django_db
class TestTags:
    def test_tags_list(self, api_client, tags):
        url = reverse("tags")
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Завтрак"
        assert data[1]["slug"] == "lunch"

    def test_single_tag(self, api_client, tags):
        tag = tags[0]
        url = reverse("tag", args=[tag.id])
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tag.id
        assert data["name"] == tag.name
        assert data["slug"] == tag.slug

    def test_single_tag_not_found(self, api_client):
        url = reverse("tag", args=[999])  # несуществующий id
        response = api_client.get(url)
        assert response.status_code == 404  # get() выбросит DoesNotExist
