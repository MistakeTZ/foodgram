from recipe.models.tag import Tag
from rest_framework import serializers


# Сериализатор тега
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
