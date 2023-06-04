from django.contrib.auth.models import User, Group
from rest_framework import serializers
from restful_server.models import BankAccount, Transaction


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class BankAccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BankAccount
        # serialized 결과에 url 을 포함하려면 명시적으로 'url' 추가해야함
        fields = ['pk', 'url', 'bank_name', 'account_name', 'account_number', 'alias', 'status', 'note']


class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    bank_name = serializers.ReadOnlyField(source='bank.bank_name')
    bank_account_name = serializers.ReadOnlyField(source='bank.account_name')
    bank_account_number = serializers.ReadOnlyField(source='bank.account_number')
    bank_alias = serializers.ReadOnlyField(source='bank.alias')

    class Meta:
        model = Transaction
        fields = [
            'bank_name',
            'bank_alias',
            'bank_account_name',
            'bank_account_number',
            'datetime',
            'user_note',
            'recipient',
            'withdraw',
            'saving',
            'balance',
            'category',
            'bank_note',
            'handler',
            'transaction_order',
            'pk',
            'url',
            'transaction_id',
        ]
        # serialized 결과에 url 을 포함하려면 명시적으로 'url' 추가해야함
