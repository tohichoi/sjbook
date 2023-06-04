from code import interact
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
from restful_server.models import BankAccount, Transaction
from restful_server.serializers import UserSerializer, GroupSerializer, BankAccountSerializer, TransactionSerializer


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


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction to be viewed or edited.

    list, retrieve, ... 기능 변경은 method 를 overwriting 해서 사용한다.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['datetime', 'recipient', 'user_note', 'category', 'bank_note', 'bank__bank_name']
    filterset_fields = {
        'datetime': ['gte', 'lte', 'exact', 'gt', 'lt'],
        'recipient': ['icontains'],
        'user_note': ['icontains'],
        'category': ['icontains'],
        'bank_note': ['icontains'],
        'bank__bank_name': ['icontains'],
    }