from django.conf.urls import include
from django.contrib import admin
from django.urls import path

from api.views import ShortLinkViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path(
        "s/<str:link>/",
        ShortLinkViewSet.as_view({"get": "short_link"}),
        name="short-link",
    ),
]
