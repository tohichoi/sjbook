from code import interact

import pendulum
from django.db.models import Min, QuerySet
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, pagination
from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend

from data_importer.common import TIMEZONE
from restful_server.datamodels import TransactionStat
from restful_server.models import BankAccount, Transaction, FAccountCategoryType, FAccountMajorCategory, \
    FAccountMinorCategory, FAccountCategory, FAccountMajorMinorCategoryLink, FAccountSubCategory
from restful_server.serializers import UserSerializer, GroupSerializer, BankAccountSerializer, TransactionSerializer, \
    FAccountCategoryTypeSerializer, FAccountMajorCategorySerializer, FAccountMinorCategorySerializer, \
    FAccountCategorySerializer, FAccountMajorMinorCategoryLinkSerializer, FAccountSubCategorySerializer, \
    TransactionFilter, TransactionStatSerializer, UploadLedgerSerializer


# from django_filters import rest_framework as filters


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # permission_classes = [permissions.IsAuthenticated]


# How to add Search functionality to a Django REST Framework powered app
# https://medium.com/swlh/searching-in-django-rest-framework-45aad62e7782
# 리스트를 customizing 할 경우 정의해서 사용
class BankAccountListAPIView(generics.ListCreateAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bank_name', 'account_name', 'account_number', 'alias']


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows BankAccount to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bank_name', 'account_name', 'account_number', 'alias']


class TransactionListAPIView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['datetime', 'recipient', 'user_note', 'category', 'bank_note', 'bank']

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


def get_daterange_queryset(request, cls):
    now = pendulum.now(tz=TIMEZONE)

    min_idate = request.query_params.get('min_date', now.start_of('month').to_date_string())
    max_idate = request.query_params.get('max_date', now.to_date_string())

    try:
        min_date = pendulum.parse(min_idate).start_of('day').in_tz(TIMEZONE)
        max_date = pendulum.parse(max_idate).end_of('day').in_tz(TIMEZONE)
    except Exception:
        return QuerySet()

    return cls.objects.filter(datetime__gte=min_date, datetime__lte=max_date)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filter_backends = (DatatablesFilterBackend,)
    # filterset_class = TransactionFilter
    #
    # search_fields = ['datetime', 'recipient', 'user_note', 'category', 'bank_note', 'bank__bank_name']
    # filterset_fields = {
    #     'datetime': ['gte', 'lte', 'exact', 'gt', 'lt'],
    #     'recipient': ['icontains'],
    #     'user_note': ['icontains'],
    #     'bank_note': ['icontains'],
    #     'bank__bank_name': ['icontains'],
    # }

    def list(self, request, *args, **kwargs):
        # queryset = User.objects.all()
        # serializer = UserSerializer(queryset, many=True)
        # return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return get_daterange_queryset(self.request, Transaction)

    # https://django-rest-framework-datatables.readthedocs.io/en/latest/tutorial.html#backend-code
    def stat(self):
        ts = TransactionStat(self.get_queryset())
        return ts.get_stat()

    class Meta:
        datatables_extra_json = ('stat',)


class TransactionStatAPIView(APIView):
    def get_queryset(self):
        return get_daterange_queryset(self.request, Transaction)

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        stat = TransactionStat(qs)
        return JsonResponse(stat.get_stat(), safe=False)


class FAccountCategoryTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = FAccountCategoryType.objects.all()
    serializer_class = FAccountCategoryTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'note']
    filterset_fields = {
        'name': ['icontains'],
        'note': ['icontains'],
    }


class FAccountMajorCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = FAccountMajorCategory.objects.all()
    serializer_class = FAccountMajorCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'note']
    filterset_fields = {
        'name': ['icontains'],
        'note': ['icontains'],
    }


class FAccountMinorCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = FAccountMinorCategory.objects.all()
    serializer_class = FAccountMinorCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'note']
    filterset_fields = {
        'name': ['icontains'],
        'note': ['icontains'],
    }


class FAccountCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = FAccountCategory.objects.all()
    serializer_class = FAccountCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'note']
    filterset_fields = {
        'name': ['icontains'],
        'note': ['icontains'],
    }


class FAccountSubCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = FAccountSubCategory.objects.all()
    serializer_class = FAccountSubCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['name', 'note']
    filterset_fields = {
        'name': ['icontains'],
        'note': ['icontains'],
    }


class FAccountMajorMinorCategoryLinkViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = FAccountMajorMinorCategoryLink.objects.all()
    serializer_class = FAccountMajorMinorCategoryLinkSerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filter_backends = [DjangoFilterBackend]
    # search_fields = ['name', 'note']
    # filterset_fields = {
    #     'name': ['icontains'],
    #     'note': ['icontains'],
    # }


class UploadLedgerAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UploadLedgerSerializer(data=request.data, request=request)
        if serializer.is_valid():
            # file_uploaded = request.FILES.get('file_uploaded')
            # content_type = file_uploaded.content_type
            # response = "POST API and you have uploaded a {} file".format(content_type)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


