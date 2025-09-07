from django.http.response import JsonResponse
from django.db import IntegrityError
from users.serializers import UserSerializer
import json


# Регистрация пользователя
def register_user(request):
    field_errors = []

    # Проверка валидности JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"field_name": ["Invalid JSON"]}, status=400)

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
    else:
        field_errors = [
            str(field[0]) for field in serializer.errors.values()]
        return JsonResponse({"field_name": field_errors}, status=400)

    # Создание пользователя
    try:
        data = {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }

        return JsonResponse(data, status=201)
    except IntegrityError:
        return JsonResponse({"field_name": [
            "Пользователь с таким email или username уже существует"]},
            status=400)
