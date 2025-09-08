from http import HTTPStatus

from api.paginator import PagePagination
from api.serializers import UserSerializer
from api.views.register import register_user
from app import constants
from django.http.response import JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from users.models import User


class UserListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        request = auth_user(request)

        paginator = PagePagination()
        paginator.page_size = request.GET.get(
            "limit", constants.PAGINATE_COUNT)
        queryset = User.objects.all()

        result_page = paginator.paginate_queryset(queryset, request)
        serializer = UserSerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        return register_user(request)


class UserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        request = auth_user(request)

        user = User.objects.filter(id=user_id).first()

        if not user:
            return JsonResponse(
                {"detail": "User does not exist"}, status=HTTPStatus.NOT_FOUND
            )

        return JsonResponse(UserSerializer(
            user, context={"request": request}
        ).data)


class MeView(APIView):
    def get(self, request):
        return JsonResponse(
            UserSerializer(request.user, context={"request": request}).data
        )


def auth_user(request):
    auth = TokenAuthentication()
    try:
        user_auth_tuple = auth.authenticate(request)
        if user_auth_tuple:
            request.user, request.auth = user_auth_tuple
    except AuthenticationFailed:
        request.user, request.auth = None, None
    finally:
        return request
