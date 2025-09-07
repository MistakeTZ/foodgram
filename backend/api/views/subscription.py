from django.http.response import JsonResponse, HttpResponse
from users.models import User
from users.models import Subscribtion
from api.serializers import UserWithRecipesSerializer
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from api.paginator import UsersPagination


# Создание/удаление подписки
@api_view(["POST", "DELETE"])
def subscribe(request, author_id):
    author = User.objects.filter(id=author_id).first()

    # Проверка существования пользователя
    if not author:
        return JsonResponse({"error": "Пользователь не найден"}, status=404)

    # Создание подписки
    if request.method == "POST":
        sub = Subscribtion.objects.filter(
            author=author, user=request.user).first()

        # Валидация подписки
        if sub:
            return JsonResponse({"error": "Подписка уже существует"},
                                status=400)
        if author == request.user:
            return JsonResponse({
                "error": "Нельзя подписаться на самого себя"
            }, status=400)
        Subscribtion.objects.create(author=author, user=request.user)
        return JsonResponse(UserWithRecipesSerializer(author,
                            context={"request": request}).data, status=201)

    # Удаление подписки
    if request.method == "DELETE":
        sub = Subscribtion.objects.filter(
            author=author, user=request.user).first()

        # Валидация подписки
        if not sub:
            return JsonResponse({"error": "Подписка не найдена"}, status=400)
        sub.delete()
        return HttpResponse(status=204)


# Получение списка подписок
@api_view(["GET"])
def subscribtions(request):
    subbed = User.objects.filter(
        id__in=Subscribtion.objects.filter(
            user=request.user).values_list("author_id", flat=True)
    )

    # Пагинация
    paginator = UsersPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(subbed, request)

    # Сериализация
    serializer = UserWithRecipesSerializer(
        result_page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)
