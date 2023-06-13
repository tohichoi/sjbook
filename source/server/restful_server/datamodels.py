from collections import OrderedDict

from django.db.models import QuerySet, Sum, F


class TransactionBankStat:
    def __init__(self, bank, bank__alias, sum_withdraw, sum_saving, sum_profit):
        self.bank = bank
        self.bank__alias = bank__alias
        self.sum_withdraw = sum_withdraw
        self.sum_saving = sum_saving
        self.sum_profit = sum_profit


class TransactionStat:
    def __init__(self, queryset, min_date, max_date, calc_stat=True):
        # self.qs: QuerySet = queryset
        self.min_date = min_date
        self.max_date = max_date
        self.qs = queryset
        self.stat = self.calc_stat(self.qs) if calc_stat else None

    def calc_stat(self):
        # 은행 계좌별로 합계를 구한다
        qs = self.qs
        stat = qs.values('bank', 'bank__alias').order_by('bank').annotate(
            sum_withdraw=Sum('withdraw'),
            sum_saving=Sum('saving')).annotate(sum_profit=F('sum_saving') - F('sum_withdraw'))
        # stat = stat.annotate(bank_pk=F('bank')).values('bank_pk')
        # stat = stat.annotate(alias=F('bank__alias')).values('alias')

        #
        # stat['sum_withdraw'] = qs.aggregate(sum=Sum('withdraw'))['sum']
        # stat['sum_saving'] = qs.aggregate(sum=Sum('saving'))['sum']
        # stat['sum_profit'] = stat['sum_saving'] - stat['sum_withdraw']
        l = list(stat.values('bank', 'bank__alias', 'sum_withdraw', 'sum_saving', 'sum_profit'))
        stat = []
        for i in l:
            stat.append(TransactionBankStat(i['bank'], i['bank__alias'], i['sum_withdraw'], i['sum_saving'], i['sum_profit']))
        self.stat = stat
        return stat
