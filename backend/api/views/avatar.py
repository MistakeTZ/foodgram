from http import HTTPStatus

from api.serializers import AvatarSerializer
from django.http.response import HttpResponse, JsonResponse
from rest_framework.decorators import api_view


@api_view(["PUT", "DELETE"])
def avatar(request):
    if request.method == "PUT":
        user = request.user

        serializer = AvatarSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(
                {"avatar": user.avatar.url},
                status=HTTPStatus.OK
            )

        return JsonResponse(
            {"field_name": [str(field[0])
                            for field in serializer.errors.values()]},
            status=HTTPStatus.BAD_REQUEST
        )

    elif request.method == "DELETE":
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return HttpResponse(status=HTTPStatus.NO_CONTENT)
