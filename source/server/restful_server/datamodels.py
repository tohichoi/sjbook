import dataclasses
from collections import OrderedDict
from pathlib import Path

from django.db.models import QuerySet, Sum, F, Subquery

from restful_server.models import BankAccount, Transaction


class TransactionBankStat:
    def __init__(self, bank, sum_withdraw, sum_saving, sum_profit, balance, balance_datetime):
        self.bank = bank
        self.sum_withdraw = sum_withdraw
        self.sum_saving = sum_saving
        self.sum_profit = sum_profit
        self.balance = balance
        self.balance_datetime = balance_datetime


class TransactionStat:
    def __init__(self, queryset, min_date, max_date, calc_stat=True):
        # self.qs: QuerySet = queryset
        self.min_date = min_date
        self.max_date = max_date
        self.qs = queryset
        self.stat = self.calc_stat() if calc_stat else None

    def calc_stat(self):
        # 은행 계좌별로 합계를 구한다
        qs = self.qs
        stat = qs.values('bank__pk').order_by('bank__pk').annotate(
            sum_withdraw=Sum('withdraw'),
            sum_saving=Sum('saving')).annotate(sum_profit=F('sum_saving') - F('sum_withdraw'))
        # stat = stat.annotate(bank_pk=F('bank')).values('bank_pk')
        # stat = stat.annotate(alias=F('bank__alias')).values('alias')

        # qs = Transaction.objects.raw('''
        #     select T.id, BA.bank_name, T.balance, Max(T.datetime) from "Transaction" T
        #     inner join BankAccount BA on BA.id = T.bank_id group by BA.bank_name
        # ''')

        #
        # stat['sum_withdraw'] = qs.aggregate(sum=Sum('withdraw'))['sum']
        # stat['sum_saving'] = qs.aggregate(sum=Sum('saving'))['sum']
        # stat['sum_profit'] = stat['sum_saving'] - stat['sum_withdraw']
        l = list(stat.values('bank__pk', 'sum_withdraw', 'sum_saving', 'sum_profit'))
        stat = []
        for i in l:
            ba = BankAccount.objects.get(pk=i['bank__pk'])
            balance = qs.filter(bank=ba).order_by('-datetime').first().balance
            balance_datetime = qs.filter(bank=ba).order_by('-datetime').first().datetime
            stat.append(TransactionBankStat(ba, i['sum_withdraw'], i['sum_saving'], i['sum_profit'],
                                            balance, balance_datetime))
        self.stat = stat
        return stat


@dataclasses.dataclass
class UploadedLedgerData:
    filename: Path
    result: int
    number_of_inserted_records: OrderedDict
