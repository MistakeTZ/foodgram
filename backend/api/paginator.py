from app import constants
from rest_framework.pagination import PageNumberPagination


class PagePagination(PageNumberPagination):
    page_size = constants.PAGINATE_COUNT
    page_size_query_param = "page_size"
    max_page_size = constants.MAX_PAGE_SIZE
