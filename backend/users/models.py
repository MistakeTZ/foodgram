from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


def user_avatar_path(instance, filename):
    return f"images/avatars/user_{instance.id}/{filename}"


class User(AbstractUser):
    username = models.CharField(
        max_length=settings.MAX_USERNAME_LENGTH,
        unique=True,
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("Пользователь с таким именем уже существует."),
        },
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        max_length=settings.MAX_EMAIL_LENGTH,
    )
    first_name = models.CharField(max_length=settings.MAX_FIRST_NAME_LENGTH)
    last_name = models.CharField(max_length=settings.MAX_LAST_NAME_LENGTH)
    password = models.CharField(max_length=settings.MAX_PASSWORD_LENGTH)
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} → {self.author}'
