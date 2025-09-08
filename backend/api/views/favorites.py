from api.views.user_reciepe_relation import handle_user_recipe_relation
from rest_framework.decorators import api_view
from api.serializers import FavoriteSerializer


@api_view(["POST", "DELETE"])
def favorite(request, recipe_id):
    return handle_user_recipe_relation(
        request, recipe_id,
        serializer_class=FavoriteSerializer,
        already_exists_msg="Рецепт уже в избранном",
        not_in_relation_msg="Рецепт не в избранном"
    )
