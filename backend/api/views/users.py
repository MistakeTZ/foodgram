from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users.models import User
from api.views.register import register_user
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from users.serializers import UserSerializer
from api.paginator import UsersPagination
from users.auth import auth_user


# Обработка запроса /users/
class UserListView(ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    # Получение списка пользователей
    def get(self, request):
        request = auth_user(request)

        paginator = UsersPagination()
        paginator.page_size = 10
        queryset = User.objects.all()

        # Пагинация
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = UserSerializer(
            result_page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    # Создание пользователя
    def post(self, request):
        return register_user(request)


# Получение пользователя
class UserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    # Получение списка пользователей
    def get(self, request, user_id):
        request = auth_user(request)

        user = User.objects.filter(id=user_id).first()

        if not user:
            return JsonResponse({"detail": "User does not exist"}, status=404)

        return JsonResponse(UserSerializer(
            user, context={"request": request}).data)


# Получение моего профиля
class MeView(APIView):
    def get(self, request):
        print(request.user)
        return JsonResponse(UserSerializer(
            request.user, context={"request": request}).data)
