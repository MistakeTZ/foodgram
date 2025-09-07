from http import HTTPStatus

from api.paginator import UsersPagination
from api.serializers.recipe import UserWithRecipesSerializer
from api.serializers.subscription import SubscribtionSerializer
from django.db.models import Count
from django.http.response import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from users.models import Subscribtion, User


class SubscribeView(APIView):
    def post(self, request, author_id):
        author = (
            User.objects.filter(id=author_id)
            .annotate(recipes_count=Count("recipes"))
            .first()
        )

        if not author:
            return JsonResponse(
                {"error": "Пользователь не найден"},
                status=HTTPStatus.NOT_FOUND
            )

        # Валидация подписки
        if Subscribtion.objects.filter(
            author=author,
            user=request.user
        ).exists():
            return JsonResponse(
                {"error": "Подписка уже существует"},
                status=HTTPStatus.BAD_REQUEST
            )

        if author == request.user:
            return JsonResponse(
                {"error": "Нельзя подписаться на самого себя"},
                status=HTTPStatus.BAD_REQUEST,
            )

        serializer = SubscribtionSerializer(
            data={"author": author.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return JsonResponse(
            UserWithRecipesSerializer(
                author, context={"request": request}).data,
            status=HTTPStatus.CREATED,
        )

    def delete(self, request, author_id):
        author = User.objects.filter(id=author_id).first()

        if not author:
            return JsonResponse(
                {"error": "Пользователь не найден"},
                status=HTTPStatus.NOT_FOUND
            )

        # Удаление подписки
        deleted, _ = Subscribtion.objects.filter(
            author=author, user=request.user
        ).delete()

        if not deleted:
            return JsonResponse(
                {"error": "Подписка не найдена"}, status=HTTPStatus.BAD_REQUEST
            )
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


# Получение списка подписок
@api_view(["GET"])
def subscribtions(request):
    subbed = User.objects.filter(
        id__in=Subscribtion.objects.filter(user=request.user).values_list(
            "author_id", flat=True
        )
    ).annotate(recipes_count=Count("recipes"))

    # Пагинация
    paginator = UsersPagination()
    if request.GET.get("limit"):
        paginator.page_size = request.GET.get("limit")
    result_page = paginator.paginate_queryset(subbed, request)

    # Сериализация
    serializer = UserWithRecipesSerializer(
        result_page, many=True, context={"request": request}
    )
    return paginator.get_paginated_response(serializer.data)
