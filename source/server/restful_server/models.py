import datetime as datetime
from django.db import models
from config import banks_conf, faccount_conf

MAX_CHAR_FIELD_LENGTH = 128
MAX_NOTE_FIELD_LENGTH = 1024


class BankAccountBase(models.Model):
    ACTIVE = banks_conf['constants']['bankaccount']['status']['ACTIVE']
    DEACTIVE = banks_conf['constants']['bankaccount']['status']['DEACTIVE']
    REVOKED = banks_conf['constants']['bankaccount']['status']['REVOKED']
    STATUS_CHOICES = [
        (ACTIVE, '사용중'),
        (DEACTIVE, '미사용'),
        (REVOKED, '해지'),
    ]

    bank_name = models.CharField(verbose_name='은행명', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True,
                                 default=None)
    account_name = models.CharField(verbose_name='예금주', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, null=True,
                                    default=None)
    account_number = models.CharField(verbose_name='은행명', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, null=True,
                                      default=None)
    alias = models.CharField(verbose_name='별칭', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    status = models.IntegerField(verbose_name='상태', blank=False, default=ACTIVE,
                                 choices=STATUS_CHOICES)
    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True, default=None)

    class Meta:
        abstract = True


class BankAccount(BankAccountBase):
    class Meta:
        managed = True
        db_table = 'BankAccount'
        ordering = ['bank_name', 'status']


class TransactionBase(models.Model):
    transaction_order = models.IntegerField('순서', blank=False, default=None)
    datetime = models.DateTimeField('거래시각', blank=False, default=datetime.datetime.now)
    withdraw = models.IntegerField('출금액', blank=True, default=None)
    saving = models.IntegerField('입금액', blank=True, default=None)
    balance = models.IntegerField('잔액', blank=False, default=None)
    recipient = models.CharField('받는분', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    user_note = models.CharField('사용자메모', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    category = models.CharField('분류', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    handler = models.CharField('처리점', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    bank_note = models.CharField('적요', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    norm_name = models.CharField('정규화이름', max_length=MAX_CHAR_FIELD_LENGTH, blank=True, null=True, default=None)
    transaction_id = models.CharField('거래고유번호', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None,
                                      unique=True)
    bank = models.ForeignKey('BankAccount', verbose_name='은행', on_delete=models.DO_NOTHING, blank=False, null=True,
                             default=None)
    faccount_category = models.ForeignKey('FAccountCategory', verbose_name='계정유형', on_delete=models.DO_NOTHING,
                                          blank=True, null=True, default=None)

    class Meta:
        abstract = True


class Transaction(TransactionBase):
    class Meta:
        managed = True
        db_table = 'Transaction'
        ordering = ['datetime', 'transaction_order', 'bank']


class FAccountSubCategory(models.Model):
    # 계정명 뒤에 붙는 세부항목(is_null=True)
    name = models.CharField('세부항목', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None, unique=True)
    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True, default=None)
    account = models.ForeignKey('FAccountCategory', verbose_name='계정', on_delete=models.DO_NOTHING, blank=True,
                                default=None)

    class Meta:
        db_table = 'FAccountSubCategoryType'

    def __str__(self):
        return self.name


class FAccountCategory(models.Model):
    # 계정명
    name = models.CharField('계정', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None)
    norm_name = models.CharField('정규화계정', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None)
    minor_category = models.ForeignKey('FAccountMinorCategory', verbose_name='중분류계정', on_delete=models.DO_NOTHING,
                                       blank=False, default=None)
    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True, default=None)

    class Meta:
        db_table = 'FAccountCategory'
        constraints = [models.UniqueConstraint(fields=['name', 'norm_name', 'minor_category'], name='core_major')]

    def __str__(self):
        return self.norm_name


class FAccountMinorCategory(models.Model):
    # 중분류
    name = models.CharField('중분류계정', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None, unique=True)

    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True)

    class Meta:
        db_table = 'FAccountMinorCategory'

    def __str__(self):
        return self.name


class FAccountMajorCategory(models.Model):
    # 대분류
    name = models.CharField('대분류계정', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None)
    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True)
    category_type = models.ForeignKey('FAccountCategoryType', verbose_name='계정유형', on_delete=models.DO_NOTHING,
                                      blank=False, default=None)

    class Meta:
        db_table = 'FAccountMajorCategory'
        constraints = [models.UniqueConstraint(fields=['name', 'category_type'], name='name_account_type')]

    def __str__(self):
        return self.name


class FAccountMajorMinorCategoryLink(models.Model):
    # 대분류
    minor_category = models.ForeignKey('FAccountMinorCategory', verbose_name='중분류계정', on_delete=models.DO_NOTHING,
                                       blank=False, default=None)
    major_category = models.ForeignKey('FAccountMajorCategory', verbose_name='대분류계정', on_delete=models.DO_NOTHING,
                                       blank=False, default=None)

    class Meta:
        db_table = 'FAccountMajorMinorCategoryLink'
        constraints = [models.UniqueConstraint(fields=['major_category', 'minor_category'], name='major_minor')]

    def __str__(self):
        return self.name


class FAccountCategoryType(models.Model):
    # 입급, 출금
    WITHDRAW = faccount_conf['constants']['faccount']['type']['WITHDRAW']
    SAVING = faccount_conf['constants']['faccount']['type']['SAVING']
    ETC = faccount_conf['constants']['faccount']['type']['ETC']
    STATUS_CHOICES = [
        (1, '지출'),
        (2, '입금'),
        (9, '기타'),
    ]

    name = models.CharField('유형', max_length=MAX_CHAR_FIELD_LENGTH, choices=STATUS_CHOICES, default=WITHDRAW,
                            blank=False, unique=True)
    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True)

    class Meta:
        db_table = 'FAccountCategoryType'

    def __str__(self):
        return self.name


class Counterpart(models.Model):
    name = models.CharField('거래처', max_length=MAX_CHAR_FIELD_LENGTH, blank=False, default=None)

    class Meta:
        db_table = 'Counterpart'

    def __str__(self):
        return self.name


class Book(models.Model):
    account_category = models.ForeignKey('FAccountCategory', verbose_name='계정', on_delete=models.DO_NOTHING,
                                         blank=False, default=None)
    counterpart = models.ForeignKey('Counterpart', verbose_name='거래처', on_delete=models.DO_NOTHING,
                                    blank=False, default=None)
    note = models.TextField(verbose_name='메모', max_length=MAX_NOTE_FIELD_LENGTH, blank=True, null=True)

    class Meta:
        db_table = 'Book'

    def __str__(self):
        return f'{self.account_category}/{self.counterpart}'
