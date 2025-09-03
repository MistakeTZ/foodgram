from django.http.response import JsonResponse
from django.contrib.auth.models import User
import re
import json


# Регистрация пользователя
def register_user(request):
    field_errors = []

    # Проверка валидности JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"field_name": ["Invalid JSON"]}, status=400)

    # Проверка email
    try:
        email = data["email"]
        valid = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

        if not valid.match(email):
            raise ValueError("Некорректный email")

        if len(email) > 254:
            raise ValueError("Email слишком длинный")
    except:
        field_errors.append("Некорректный email")

    # Проверка username
    try:
        username = data["username"]
        valid = re.compile(r"^[\w.@+-]+\Z")

        if not valid.match(username):
            raise ValueError("Username некорректный")
        if len(username) > 150:
            raise ValueError("Username слишком длинный")
    except:
        field_errors.append("Некорректный username")

    # Проверка имени
    try:
        first_name = data["first_name"]

        if len(first_name) > 150:
            raise ValueError("Имя слишком длинное")
    except:
        field_errors.append("Некорректное имя")

    # Проверка фамилии
    try:
        last_name = data["last_name"]

        if len(last_name) > 150:
            raise ValueError("Фамилия слишком длинная")
    except:
        field_errors.append("Некорректная фамилия")

    # Проверка пароля
    try:
        password = data["password"]

        if len(password) > 128:
            raise ValueError("Пароль слишком длинный")
        if len(password) < 8:
            raise ValueError("Пароль слишком короткий")
        if not re.search("[a-z]", password):
            if not re.search("[A-Z]", password):
                raise ValueError("Пароль должен содержать букву")
        if not re.search("[0-9]", password):
            raise ValueError("Пароль должен содержать цифру")
    except ValueError as e:
        field_errors.append(str(e))
    except:
        field_errors.append("Некорректный пароль")

    # Возврат ошибкок
    if field_errors:
        return JsonResponse({"field_name": field_errors}, status=400)

    # Создание пользователя
    try:
        user = User.objects.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        data = {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }

        return JsonResponse(data, status=201)
    except Exception as e:
        return JsonResponse({"field_name": ["Пользователь с таким email или username уже существует"]}, status=400)
