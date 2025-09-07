from rest_framework import serializers
from users.models import Subscribtion


class SubscribtionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribtion
        fields = ("author", "user")
        extra_kwargs = {"user": {"read_only": True}}
