from http import HTTPStatus

from api.serializers.tag import TagSerializer
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from recipe.models.tag import Tag


# Получение списка тегов
@require_GET
def tags(request):
    tag_list = TagSerializer(Tag.objects.all(), many=True).data

    return JsonResponse(tag_list, safe=False)


# Получение конкретного тега
@require_GET
def tag(request, tag_id):
    tag = Tag.objects.filter(id=tag_id).first()
    if not tag:
        return JsonResponse(
            {"detail": "Тег не найден"},
            status=HTTPStatus.NOT_FOUND
        )
    return JsonResponse(TagSerializer(tag).data)
