from django.urls import path
from .views import link


urlpatterns = [
    path('<str:link>/', link.short_link, name='short_link'),
]
