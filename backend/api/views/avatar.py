import base64
import json
from http import HTTPStatus
from uuid import uuid4

from django.core.files.base import ContentFile
from django.http.response import HttpResponse, JsonResponse
from rest_framework.decorators import api_view


# Изменение аватара
@api_view(["PUT", "DELETE"])
def avatar(request):
    # Установка аватара
    if request.method == "PUT":
        user = request.user

        # Проверка валидности JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"field_name": ["Invalid JSON"]}, status=HTTPStatus.BAD_REQUEST
            )

        try:
            # Получение изображения
            image = data["avatar"]
            format, imgstr = image.split(";base64,")
            ext = format.split("/")[-1]
            file_name = f"{uuid4()}.{ext}"

            # Сохранение изображения
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
            user.avatar.save(file_name, data, save=True)

            return JsonResponse({"avatar": user.avatar.url})
        except KeyError:
            return JsonResponse(
                {"field_name": ["Аватар не найден"]},
                status=HTTPStatus.BAD_REQUEST
            )

    # Удаление аватара
    elif request.method == "DELETE":
        user = request.user
        user.avatar = None
        user.save()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
