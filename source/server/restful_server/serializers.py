import re
import shutil
import warnings
from collections import OrderedDict
from pathlib import Path
from zoneinfo import ZoneInfo

import pendulum
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django_filters import widgets, fields, filters
from openpyxl.reader.excel import load_workbook
from rest_framework import serializers
from rest_framework.fields import FileField
from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet
from xlrd import open_workbook

from config import banks_conf, backend_conf
from data_importer.common import TIMEZONE
from data_importer.database import open_database, query_count, import_transaction_data
from data_importer.transaction import load_transaction_data
from restful_server.datamodels import TransactionStat, TransactionBankStat, UploadedLedgerData
from restful_server.models import BankAccount, Transaction, FAccountCategory, FAccountMajorCategory, \
    FAccountCategoryType, FAccountMinorCategory, FAccountSubCategory, FAccountMajorMinorCategoryLink


class GlobalCharFilter(GlobalFilter, filters.CharFilter):
    pass


class GlobalNumberFilter(GlobalFilter, filters.NumberFilter):
    pass


class YADCFMultipleChoiceWidget(widgets.QueryArrayWidget):
    def value_from_datadict(self, data, files, name):
        if name not in data:
            return None
        vals = data[name].split("|")
        new_data = data.copy()
        new_data[name] = vals
        return super().value_from_datadict(new_data, files, name)


class YADCFModelMultipleChoiceField(fields.ModelMultipleChoiceField):
    widget = YADCFMultipleChoiceWidget


class YADCFModelMultipleChoiceFilter(filters.ModelMultipleChoiceFilter):
    field_class = YADCFModelMultipleChoiceField

    def global_q(self):
        """
        This method is necessary for the global filter
        - i.e. any string values entered into the search box.
        """
        if not self._global_search_value:
            return Q()
        kw = "{}__{}".format(self.field_name, self.lookup_expr)
        return Q(**{kw: self._global_search_value})


class TransactionFilter(DatatablesFilterSet):
    # the name of this attribute must match the declared 'data' attribute in
    # the DataTables column
    artist_name = YADCFModelMultipleChoiceFilter(
        field_name="name", queryset=Transaction.objects.all(), lookup_expr="contains"
    )

    # additional attributes need to be declared so that sorting works
    # the field names must match those declared in the DataTables columns.
    rank = GlobalNumberFilter()
    name = GlobalCharFilter()

    class Meta:
        model = Transaction
        fields = ("name", "norm_name", "recipient", "bank_note", "user_note")


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


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


class BankAccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BankAccount
        # serialized 결과에 url 을 포함하려면 명시적으로 'url' 추가해야함
        fields = ['pk', 'url', 'bank_name', 'account_name', 'account_number', 'alias', 'status', 'note']


class TransactionBankStatSerializer(serializers.Serializer):
    bank = BankAccountSerializer(many=False, read_only=True)
    # bank__alias = serializers.CharField()
    sum_withdraw = serializers.IntegerField()
    sum_saving = serializers.IntegerField()
    sum_profit = serializers.IntegerField()
    balance = serializers.IntegerField()
    balance_datetime = serializers.DateTimeField()

    class Meta:
        fields = ['bank', 'sum_withdraw', 'sum_saving', 'sum_profit']

    def validate(self, data):
        try:
            BankAccount.objects.get(pk=data['bank'].pk)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"bank {data['bank']} not found")
        return data


class TransactionStatSerializer(serializers.Serializer):
    min_date = serializers.DateTimeField(default_timezone=ZoneInfo(TIMEZONE))
    max_date = serializers.DateTimeField(default_timezone=ZoneInfo(TIMEZONE))
    stat = TransactionBankStatSerializer(many=True, read_only=False)

    class Meta:
        fields = ['min_date', 'max_date', 'stat']


class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    bank = BankAccountSerializer(many=False, read_only=True)
    # bank_alias = serializers.ReadOnlyField(source='bank.alias')
    faccount_category = FAccountCategorySerializer(many=False, read_only=True)
    # faccount_category = serializers.ReadOnlyField(source='faccount_category.norm_name')
    # bank_name = serializers.ReadOnlyField(source='bank.bank_name')
    # bank_account_name = serializers.ReadOnlyField(source='bank.account_name')
    # bank_account_number = serializers.ReadOnlyField(source='bank.account_number')
    # If you want, you can add special fields understood by Datatables,
    # the fields starting with DT_Row will always be serialized.
    # See: https://datatables.net/manual/server-side#Returned-data
    DT_RowId = serializers.SerializerMethodField()
    DT_RowAttr = serializers.SerializerMethodField()

    def get_DT_RowId(self, album):
        return 'row_%d' % album.pk

    def get_DT_RowAttr(self, album):
        return {'data-pk': album.pk}
    
    class Meta:
        model = Transaction
        fields = [
            'DT_RowId',
            'DT_RowAttr',
            'bank',
            'faccount_category',
            'recipient',
            'datetime',
            'withdraw',
            'saving',
            'balance',
            'bank_note',
            'user_note',
            # 'bank_name',
            # 'bank_account_name',
            # 'bank_account_number',
            'handler',
            # 'url',
            'transaction_order',
            'pk',
            'transaction_id',
        ]
        # serialized 결과에 url 을 포함하려면 명시적으로 'url' 추가해야함
        datatables_always_serialize = ('pk',)


def validate_excel_file(value):
    try:
        load_workbook(filename=value)
        is_xlsx = True
    except Exception:
        is_xlsx = False

    try:
        open_workbook(value)
        is_xls = True
    except Exception:
        is_xls = False

    if not is_xlsx and not is_xls:
        impf = {
            'filename': value.name,
            'result': -1,
            'message': '지원되지 않는 파일 형식입니다.',
            'number_of_inserted_records': OrderedDict({
                'bankaccounts': 0,
                'transactions': 0,
            })}
        raise serializers.ValidationError(impf)


# class ImportedFileSerializer(serializers.Serializer):
#     filename = serializers.CharField()
#     result: serializers.IntegerField()
#     number_of_inserted_records: serializers.DictField(child=serializers.IntegerField())


class UploadedLedgerSerializer(serializers.Serializer):
    filename = serializers.CharField()
    result = serializers.IntegerField()
    message = serializers.CharField()
    number_of_inserted_records = serializers.DictField(child=serializers.IntegerField())

    def __init__(self, instance=None, data=None, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(instance, data, **kwargs)

    def _get_user_dirname(self):
        if self.request.user.is_anonymous:
            return 'anonymous'
        return str(self.request.user.pk)

    def _save_file(self, f: UploadedFile):
        # f: <InMemoryUploadedFile: KB_logo.svg (image/svg+xml)>
        file_name = f.name
        user_dir = self._get_user_dirname()
        dest_dir = Path(banks_conf['data']['root']) / Path(f'queue/{user_dir}')
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)

        local_file = dest_dir / Path(file_name)
        with open(local_file, 'wb+') as fd:
            for chunk in f.chunks():
                fd.write(chunk)

        return local_file

    def _import_ledgers(self, path):
        p = Path(path)
        if not p.match(banks_conf['data']['rglob_pattern']):
            impf = {
                'filename': p.name,
                'result': -1,
                'message': '은행 거래내역 파일 형식이 아닙니다.',
                'number_of_inserted_records': OrderedDict({
                    'bankaccounts': 0,
                    'transactions': 0,
                })}
            return impf

        try:
            conn, cur = open_database()
            db_nbad_before = query_count(cur, 'id', 'BankAccount')
            db_ntrd_before = query_count(cur, 'id', 'Transaction')

            trs = load_transaction_data([p])
            # nbad : # of inserted band account records
            # ntrd : # of inserted transaction records
            nbad, ntrd = import_transaction_data(trs)

            db_nbad_after = query_count(cur, 'id', 'BankAccount')
            db_ntrd_after = query_count(cur, 'id', 'Transaction')

            # nbad == db_nbad_after - db_nbad_before
            # ntrd == db_ntrd_after - db_ntrd_before

            impf = {
                'filename': p.name,
                'result': nbad + ntrd,
                'message': f'{nbad}개의 은행계정과 {ntrd}개의 거래내역을 가져왔습니다.',
                'number_of_inserted_records': OrderedDict({
                    'bankaccounts': nbad,
                    'transactions': ntrd,
                })}
            return impf
        except Exception as e:
            return {
                'filename': p.name,
                'result': -1,
                'message': e.args,
                'number_of_inserted_records': OrderedDict({
                    'bankaccounts': 0,
                    'transactions': 0,
                })}

    def _archive_file(self, local_file: Path):
        root = backend_conf['server']['archive_file_root']
        user_dir = self._get_user_dirname()
        dest_dir = root / Path(user_dir)
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True)
        prefix = re.sub('[-:\+]', '', pendulum.now("UTC").to_w3c_string())
        new_file = dest_dir / local_file.with_stem(f'{prefix}-{local_file.with_suffix("").name}').name
        shutil.move(local_file, new_file)

    def validate(self, attrs):
        return super().validate(attrs)
        # return attrs

    def _handle_uploaded_file(self, f: UploadedFile):
        # try:
        local_file = self._save_file(f)
        validate_excel_file(local_file)
        impf = self._import_ledgers(local_file)
        if impf['result'] > 0:
            self._archive_file(local_file)

        return impf
        # except Exception as e:
        #     raise serializers.ValidationError(f'Cannot save file {f}')

    # https://www.django-rest-framework.org/api-guide/serializers/#read-write-baseserializer-classes
    def to_internal_value(self, data):
        ret = self._handle_uploaded_file(data['file'])

        # returns OrderedDict
        return ret

    class Meta:
        fields = ['file_uploaded']
