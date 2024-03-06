# DRF Library
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    A custom pagination class for handling pagination in API responses.

    This class extends the PageNumberPagination
    class from Django Rest Framework
    to customize the pagination behavior.
    It sets a default page size, specifies
    the query parameters for pagination, and defines a maximum page size.

    Attributes
    ----------
    page_size : int
        The default number of items to display per page. Default is 10.
    page_query_param : str
        The query parameter name for specifying the page number.
        Default is 'page'.
    page_size_query_param : str
        The query parameter name for specifying the number of items per page.
        Default is 'limit'.
    max_page_size : int
        The maximum number of items that can be requested per page.
        Default is 100.
    """
    page_size: int = 10
    page_query_param: str = 'page'
    page_size_query_param: str = 'limit'
    max_page_size: int = 100
