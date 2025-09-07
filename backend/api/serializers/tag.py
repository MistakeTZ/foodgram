from rest_framework import serializers
from recipe.models.tag import Tag


# Сериализатор тега
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
