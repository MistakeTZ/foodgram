from django.contrib import admin
from users.models import User, Subscribtion


# Регистрация ингредиента
@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email', 'first_name', 'last_name')


# Регистрация подписки
admin.site.register(Subscribtion)
