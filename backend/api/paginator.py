from django.http.response import JsonResponse
from rest_framework.pagination import PageNumberPagination
from django.conf import settings


# Пагинация пользователей
class UsersPagination(PageNumberPagination):
    page_size = settings.PAGINATE_COUNT
    page_size_query_param = "page_size"
    max_page_size = settings.MAX_PAGE_SIZE

    def get_paginated_response(self, data):
        return JsonResponse({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
