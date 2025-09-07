import json
from http import HTTPStatus

from django.http.response import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from users.models import User
from users.serializers import UserPasswordUpdateSerializer


@require_POST
@csrf_exempt
def login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=HTTPStatus.BAD_REQUEST
        )

    try:
        user = User.objects.get(email=data["email"])
    except User.DoesNotExist:
        return JsonResponse(
            {"error": "User does not exist"},
            status=HTTPStatus.BAD_REQUEST
        )

    try:
        valid = user.check_password(data["password"])

        if not valid:
            raise ValueError
    except ValueError:
        return JsonResponse(
            {"error": "Неверный пароль"},
            status=HTTPStatus.BAD_REQUEST
        )

    token, created = Token.objects.get_or_create(user=user)
    return JsonResponse({"auth_token": token.key}, status=HTTPStatus.OK)


@api_view(["POST"])
def logout(request):
    Token.objects.get(user=request.user).delete()
    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@api_view(["POST"])
def set_password(request):
    user = request.user

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"field_name": ["Invalid JSON"]}, status=HTTPStatus.BAD_REQUEST
        )

    serializer = UserPasswordUpdateSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        return JsonResponse(
            {
                "field_name": [
                    str(field[0]) for field in list(serializer.errors.values())
                ]
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    return HttpResponse(status=HTTPStatus.NO_CONTENT)
