from pathlib import Path

from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import UploadedFile
from django_filters import widgets, fields, filters
from openpyxl.reader.excel import load_workbook
from rest_framework import serializers
from rest_framework.fields import FileField
from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet
from xlrd import open_workbook

from config import banks_conf
from restful_server.datamodels import TransactionStat
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


class TransactionStatSerializer(serializers.BaseSerializer):
    sum_profit = serializers.IntegerField(read_only=True)
    sum_withdraw = serializers.IntegerField()
    sum_saving = serializers.IntegerField()

    def to_representation(self, instance):
        # return super().to_representation(instance)
        return instance.get_stat()

    class Meta:
        model = TransactionStat
        fields = ['sum_profit', 'sum_withdraw', 'sum_saving']


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
        raise serializers.ValidationError("유효한 형식의 엑셀파일이 아닙니다.")


class UploadLedgerSerializer(serializers.Serializer):
    file_uploaded = FileField(validators=[validate_excel_file, ])

    def __init__(self, instance=None, data=None, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(instance, data, **kwargs)

    def _handle_uploaded_file(self, f: UploadedFile):
        # f: <InMemoryUploadedFile: KB_logo.svg (image/svg+xml)>
        file_name = f.name
        if self.request.user.is_anonymous:
            user_dir = 'anonymous'
        else:
            user_dir = str(self.request.user.pk)
        dest_dir = Path(banks_conf['data']['root']) / Path(f'queue/{user_dir}')
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)

        local_file = dest_dir / Path(file_name)
        with open(local_file, 'wb+') as fd:
            for chunk in f.chunks():
                fd.write(chunk)

        return True

    def to_internal_value(self, data):
        self._handle_uploaded_file(data['file'])
        # returns OrderedDict
        return {'file_uploaded': 'OK'}

    class Meta:
        fields = ['file_uploaded']
