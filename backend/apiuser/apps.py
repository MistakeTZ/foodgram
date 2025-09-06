from django.apps import AppConfig


# Создание профиля пользователя
class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apiuser'

    def ready(self):
        from . import signals  # noqa: F401
