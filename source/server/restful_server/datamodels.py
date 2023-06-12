from collections import OrderedDict

from django.db.models import QuerySet, Sum, F


class TransactionStat:
    def __init__(self, queryset):
        self.qs: QuerySet = queryset
        self.get_stat()

    def get_stat(self):
        qs = self.qs

        # 은행 계좌별로 합계를 구한다
        stat = qs.values('bank', 'bank__alias').order_by('bank').annotate(
            sum_withdraw=Sum('withdraw'),
            sum_saving=Sum('saving')).annotate(sum_profit=F('sum_saving') - F('sum_withdraw'))
        # stat = stat.annotate(bank_pk=F('bank')).values('bank_pk')
        # stat = stat.annotate(alias=F('bank__alias')).values('alias')

        #
        # stat['sum_withdraw'] = qs.aggregate(sum=Sum('withdraw'))['sum']
        # stat['sum_saving'] = qs.aggregate(sum=Sum('saving'))['sum']
        # stat['sum_profit'] = stat['sum_saving'] - stat['sum_withdraw']

        return 'stat', list(stat.values('bank', 'bank__alias', 'sum_withdraw', 'sum_saving', 'sum_profit'))
