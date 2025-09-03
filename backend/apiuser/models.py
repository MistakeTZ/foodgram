from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


# Путь сохранения аватара
def user_avatar_path(instance, filename):
    return f"images/avatars/user_{instance.user.id}/{filename}"


# Модель профиля
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.avatar.url


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
