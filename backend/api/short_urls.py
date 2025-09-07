from api.views import link
from django.urls import path

urlpatterns = [
    path("<str:link>/", link.short_link, name="short_link"),
]
