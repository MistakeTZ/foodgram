from django.http import JsonResponse
from ..models.tag import Tag
from ..serializers import TagSerializer
from django.views.decorators.http import require_GET


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
        return JsonResponse({"detail": "Тег не найден"}, status=404)
    return JsonResponse(TagSerializer(tag).data)
