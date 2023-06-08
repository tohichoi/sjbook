from django.contrib.auth.models import User, Group
from rest_framework import serializers
from restful_server.models import BankAccount, Transaction, FAccountCategory, FAccountMajorCategory, \
    FAccountCategoryType, FAccountMinorCategory, FAccountSubCategory, FAccountMajorMinorCategoryLink


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
    faccount_category = serializers.ReadOnlyField(source='faccount_category.name')

    class Meta:
        model = Transaction
        fields = [
            'bank_alias',
            'faccount_category',
            'recipient',
            'datetime',
            'withdraw',
            'saving',
            'balance',
            'bank_note',
            'user_note',
            'bank_name',
            'bank_account_name',
            'bank_account_number',
            'handler',
            'url',
            'transaction_order',
            'pk',
            'transaction_id',
        ]
        # serialized 결과에 url 을 포함하려면 명시적으로 'url' 추가해야함


class FAccountMinorCategorySerializer(serializers.HyperlinkedModelSerializer):
    # category_type = FAccountMinorCategorySerializer(many=True, read_only=True)

    class Meta:
        model = FAccountMinorCategory
        fields = [
            'pk',
            'name',
            'note',
        ]


class FAccountMajorCategorySerializer(serializers.HyperlinkedModelSerializer):
    minor_category = FAccountMinorCategorySerializer(many=True, read_only=True)

    class Meta:
        model = FAccountMajorCategory
        fields = [
            'pk',
            'name',
            'note',
            'category_type',
            'minor_category'
        ]


class FAccountCategoryTypeSerializer(serializers.HyperlinkedModelSerializer):
    # major_categories = serializers.ReadOnlyField(source='faccountmajorcategory_set')
    # major_categories = FAccountMajorCategorySerializer(many=True, read_only=True)

    class Meta:
        model = FAccountCategoryType
        fields = [
            'pk',
            'name',
            'note',
            # 'major_categories'
        ]


class FAccountCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FAccountCategory
        fields = [
            'pk',
            'name',
            'norm_name',
            'note',
            'minor_category'
        ]


class FAccountSubCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FAccountSubCategory
        fields = [
            'pk',
            'name',
            'note',
            'account'
        ]


class FAccountMajorMinorCategoryLinkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FAccountMajorMinorCategoryLink
        fields = [
            'pk',
            'minor_category',
            'major_category',
        ]


