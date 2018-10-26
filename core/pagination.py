from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class NamedPageNumberPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data, name='results', unfiltered_count=0, success=True):
        return Response(OrderedDict([
            ('success', True),
            ('count', self.page.paginator.count),
            ('unfiltered_count', unfiltered_count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            (name, data)
        ]))