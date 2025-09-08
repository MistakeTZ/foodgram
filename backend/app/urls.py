from api.views import link
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("s/<str:link>/", link.short_link, name="short_link"),
]
