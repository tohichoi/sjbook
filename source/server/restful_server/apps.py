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
            'page_count': self.max_page_size,
            'count': self.page.paginator.count,
            'results': data
        })
