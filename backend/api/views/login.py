from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from users.models import User
from users.serializers import UserPasswordUpdateSerializer
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
        return JsonResponse({"error": "Неверный пароль"}, status=400)

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
            "field_name": ["Invalid JSON"]},
            status=400)

    serializer = UserPasswordUpdateSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        return JsonResponse({"field_name": [str(field[0]) for field in list(
            serializer.errors.values())]}, status=400)

    return HttpResponse(status=204)
