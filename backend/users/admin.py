from django.contrib import admin
from users.models import Subscribtion, User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ("username", "email", "first_name", "last_name")


admin.site.register(Subscribtion)
