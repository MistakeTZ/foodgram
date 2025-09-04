from django.http.response import JsonResponse, HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from ..models import Profile
import json
import base64
from uuid import uuid4


# Изменение аватара
@api_view(["PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def avatar(request):
    # Установка аватара
    if request.method == "PUT":
        user = request.user

        # Проверка валидности JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"field_name": ["Invalid JSON"]}, status=400)

        try:
            # Получение профиля
            profile = Profile.objects.get(user=user)

            # Получение изображения
            image = data["avatar"]
            format, imgstr = image.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"{uuid4()}.{ext}"

            # Сохранение изображения
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
            profile.avatar.save(file_name, data, save=True)

            return JsonResponse({"avatar": profile.avatar.url})
        except KeyError:
            return JsonResponse(
                {"field_name": ["Аватар не найден"]}, status=400)

    # Удаление аватара
    elif request.method == "DELETE":
        user = request.user
        profile = Profile.objects.get(user=user)
        profile.avatar = None
        profile.save()
        return HttpResponse(status=204)
