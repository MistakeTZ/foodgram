from rest_framework.pagination import PageNumberPagination

from app import constants


class PagePagination(PageNumberPagination):
    page_size = constants.PAGINATE_COUNT
    page_size_query_param = "limit"
    max_page_size = constants.MAX_PAGE_SIZE
