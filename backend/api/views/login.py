from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from rest_framework.decorators import (
    authentication_classes, permission_classes, api_view)
from users.models import User
from rest_framework.authtoken.models import Token
import json
import re


# Логин пользователя
@require_POST
@csrf_exempt
def login(request):
    # Обработка невалидного JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Проверка существования пользователя
    try:
        user = User.objects.get(email=data["email"])
    except User.DoesNotExist:
        return JsonResponse({"error": "User does not exist"}, status=400)

    # Проверка пароля
    try:
        valid = user.check_password(data["password"])

        if not valid:
            raise ValueError
    except ValueError:
        return JsonResponse({"error": "Invalid password"}, status=400)

    # Генерация токена
    token, created = Token.objects.get_or_create(user=user)
    return JsonResponse({"auth_token": token.key}, status=200)


# Выход пользователя
@api_view(["POST"])
def logout(request):
    # Удаление токена
    Token.objects.get(user=request.user).delete()
    return HttpResponse(status=204)


# Изменение пароля
@api_view(["POST"])
def set_password(request):
    user = request.user

    # Обработка невалидного JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "field_name": ["Текущий пароль", "Новый пароль"]},
            status=400)

    # Проверка пароля
    valid = user.check_password(data["current_password"])
    if not valid:
        return JsonResponse({"field_name": ["Неверный пароль"]}, status=400)

    # Проверка нового пароля
    try:
        if len(data["new_password"]) > 128:
            raise ValueError("Пароль слишком длинный")
        if len(data["new_password"]) < 8:
            raise ValueError("Пароль слишком короткий")
        if not re.search("[a-z]", data["new_password"]):
            if not re.search("[A-Z]", data["new_password"]):
                raise ValueError("Пароль должен содержать хотя бы одну букву")
        if not re.search("[0-9]", data["new_password"]):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")

        # Изменение пароля
        user.set_password(data["new_password"])
        user.save()
        return HttpResponse(status=204)
    except ValueError as e:
        return JsonResponse({"field_name": [str(e)]}, status=400)
    except KeyError:
        return JsonResponse({"field_name": ["Новый пароль"]}, status=400)
