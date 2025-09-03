from django.contrib import admin
from .models import Subscribtion, Profile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

# Убирание стандартной регистрации
admin.site.unregister(User)


# Добавление поиска по полям
@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
    search_fields = ('username', 'email', 'first_name', 'last_name')


# Регистрация подписки
admin.site.register(Subscribtion)
# Регистрация профиля
admin.site.register(Profile)
