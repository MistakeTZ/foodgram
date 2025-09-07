from django.http.response import JsonResponse, HttpResponse
from users.models import User
from users.models import Subscribtion
from api.serializers.recipe import UserWithRecipesSerializer
from rest_framework.decorators import api_view
from api.paginator import UsersPagination
from django.db.models import Count
from http import HTTPStatus


# Создание/удаление подписки
@api_view(["POST", "DELETE"])
def subscribe(request, author_id):
    author = User.objects.filter(id=author_id).annotate(
        recipes_count=Count('recipes')
    ).first()

    # Проверка существования пользователя
    if not author:
        return JsonResponse({"error": "Пользователь не найден"},
                            status=HTTPStatus.NOT_FOUND)

    # Создание подписки
    if request.method == "POST":
        sub = Subscribtion.objects.filter(
            author=author, user=request.user).first()

        # Валидация подписки
        if sub:
            return JsonResponse({"error": "Подписка уже существует"},
                                status=HTTPStatus.BAD_REQUEST)
        if author == request.user:
            return JsonResponse({
                "error": "Нельзя подписаться на самого себя"
            }, status=HTTPStatus.BAD_REQUEST)
        Subscribtion.objects.create(author=author, user=request.user)
        return JsonResponse(UserWithRecipesSerializer(author,
                            context={"request": request}).data,
                            status=HTTPStatus.CREATED)

    # Удаление подписки
    if request.method == "DELETE":
        is_deleted = Subscribtion.objects.filter(
            author=author, user=request.user).delete()

        # Валидация подписки
        if not is_deleted[0]:
            return JsonResponse({"error": "Подписка не найдена"},
                                status=HTTPStatus.BAD_REQUEST)
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


# Получение списка подписок
@api_view(["GET"])
def subscribtions(request):
    subbed = User.objects.filter(
        id__in=Subscribtion.objects.filter(
            user=request.user).values_list("author_id", flat=True)
    ).annotate(recipes_count=Count('recipes'))

    # Пагинация
    paginator = UsersPagination()
    if request.GET.get("limit"):
        paginator.page_size = request.GET.get("limit")
    result_page = paginator.paginate_queryset(subbed, request)

    # Сериализация
    serializer = UserWithRecipesSerializer(
        result_page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)
