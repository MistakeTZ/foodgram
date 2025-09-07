import re

from rest_framework import serializers
from users.models import Subscribtion, User


class UserPasswordUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.instance
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль указан неверно.")

    def validate_new_password(self, value):
        return password_validation(value)

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save(update_fields=["password"])
        return instance


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
            "avatar",
        ]

    def validate_password(self, value):
        return password_validation(value)

    def validate_username(self, value):
        valid = re.compile(r"^[\w.@+-]+\Z")

        if not valid.match(value):
            raise serializers.ValidationError("Username некорректный")
        return value

    def get_is_subscribed(self, obj):
        if not self.context["request"].user.is_authenticated:
            return False
        return Subscribtion.objects.filter(
            author=obj, user=self.context["request"].user
        ).exists()


def password_validation(value):
    if len(value) > 128:
        raise serializers.ValidationError("Пароль слишком длинный")
    if len(value) < 8:
        raise serializers.ValidationError("Пароль слишком короткий")
    if not re.search("[a-z]", value):
        if not re.search("[A-Z]", value):
            raise serializers.ValidationError("Пароль должен содержать букву")
    if not re.search("[0-9]", value):
        raise serializers.ValidationError("Пароль должен содержать цифру")
    return value
