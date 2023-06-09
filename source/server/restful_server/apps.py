from django.apps import AppConfig
from rest_framework import pagination
from rest_framework.response import Response


class RestfulServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restful_server'


class CustomPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'current_page': self.page.number,
            'num_pages': self.page.paginator.num_pages,
            'item_count_per_page': self.max_page_size,
            'item_count': self.page.paginator.count,
            'data': data
        })
