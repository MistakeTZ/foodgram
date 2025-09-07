from django.contrib import admin
from users.models import Subscribtion, User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(Subscribtion)
class SubscribtionAdmin(admin.ModelAdmin):
    list_display = ("user", "author")
