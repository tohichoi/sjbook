import unittest
from pathlib import Path

import pandas as pd

from config import banks_conf, database_conf
from src.database import import_transaction_data
from src.transaction import load_transaction_data, read_ledger


class Test_database(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        data_root = Path(banks_conf['data']['root'])
        filelist = set(data_root.rglob("*.xls"))
        self.trs = load_transaction_data(filelist)

    def test_import_transaction_data(self):
        import_transaction_data(self.trs)


@unittest.skip('Passed')
class Test_transaction(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path('/home/x/Workspace/sjbook/data')

    def test_read_kb1_ledger(self):
        ledger_type = 'kb1'
        fns = ['국민환전.xls', '국민고철.xls', '국민퇴직연금.xls']
        for f in fns:
            fn = Path(self.data_root) / f
            bd = read_ledger(fn, ledger_type, banks_conf[ledger_type])
            print(bd.account_name, bd.account_number)
            print(bd.dataframe)
            self.assertGreater(bd.dataframe.shape[0], 0)

    def test_read_nh1_ledger(self):
        ledger_type = 'nh1'
        fns = ['농협관리.xls', '농협스위칭.xls', '농협원자재.xls', '농협일반경비.xls']
        for f in fns:
            fn = Path(self.data_root) / f
            bd = read_ledger(fn, ledger_type, banks_conf[ledger_type])
            print(bd.account_name, bd.account_number)
            print(bd.dataframe)
            self.assertGreater(bd.dataframe.shape[0], 0)

    @unittest.skip('done')
    def test_pandas_date_parser(self):
        fn = self.data_root / '농협일반경비.xls'
        df = pd.read_excel(fn, engine='xlrd',
                           skiprows=9,
                           usecols='B:J',
                           parse_dates=[[0, 7]],
                           date_format={0: '%Y/%m/%d', 7: '%I:%M:%S'})
        print(df)


if __name__ == '__main__':
    unittest.main()
