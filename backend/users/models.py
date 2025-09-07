from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


def user_avatar_path(instance, filename):
    return f"images/avatars/user_{instance.id}/{filename}"


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("Пользователь с таким именем уже существует."),
        },
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        max_length=254,
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=254)
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.email


# Модель подписки
class Subscribtion(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
