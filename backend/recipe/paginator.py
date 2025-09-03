from django.http.response import JsonResponse
from rest_framework.pagination import PageNumberPagination


# Пагинация рецептов
class RecipePagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return JsonResponse({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
