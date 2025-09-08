from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from api.views import link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path("s/<str:link>/", link.short_link, name="short_link"),
]
