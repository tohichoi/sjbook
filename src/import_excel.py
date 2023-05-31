import datetime
import re
import unittest

import openpyxl
import pandas as pd
from config import banks_conf
from pathlib import Path
import pendulum
import xlrd


TIMEZONE = 'Asia/Seoul'


def convert_date_kb1(v):
    # 2023.03.02 20:43:37
    # return pendulum.from_format(v, 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    dt = pendulum.from_format(v.strip(), 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    return datetime.datetime.fromisoformat(dt.to_iso8601_string())


date_converters = {
    'kb1': convert_date_kb1
}


def read_account_info(fn, ac):
    book = xlrd.open_workbook(fn)
    account_number_value = book.sheet_by_index(0).cell(ac['number_pos'][0], ac['number_pos'][1]).value
    account_name_value = book.sheet_by_index(0).cell(ac['name_pos'][0], ac['name_pos'][1]).value
    account_number = None
    account_name = None
    m = re.match(ac['number_regexp'], account_number_value)
    if m:
        account_number = m.group(1)

    m = re.match(ac['name_regexp'], account_name_value)
    if m:
        account_name = m.group(1)

    return {'account_number': account_number, 'account_name': account_name}


def read_ledger(ledger_type, data_root, ledger_conf: dict) -> (dict, pd.DataFrame):
    lc = ledger_conf
    # fn = Path(data_root) / lc['excel']['name_pattern']
    fn = Path(data_root) / '국민환전.xls'

    account_info = read_account_info(fn, lc['account'])

    df = pd.read_excel(fn, engine=lc['excel']['engine'],
                       skiprows=lc['transaction']['start_row'],
                       converters={1: date_converters[ledger_type]})

    return account_info, df


class Test(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger_type = 'kb1'
        self.data_root = '/home/x/Workspace/sjbook/data'

    def test_read_ledger(self):
        account_info, df = read_ledger(self.ledger_type, self.data_root, banks_conf[self.ledger_type])
        print(account_info)
        print(df)
        self.assertGreater(df.shape[0], 0)