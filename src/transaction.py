import dataclasses
import datetime
import re
import warnings
from pathlib import Path

import pandas as pd
from config import banks_conf
import pendulum
import xlrd

TIMEZONE = 'Asia/Seoul'


@dataclasses.dataclass
class TransactionData:
    bank_name: str
    account_name: str
    account_number: str
    alias: str
    status: str
    note: str
    dataframe: pd.DataFrame


def convert_datetime_kb1(v):
    # 2023.03.02 20:43:37
    # return pendulum.from_format(v, 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    dt = pendulum.from_format(v.strip(), 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    return datetime.datetime.fromisoformat(dt.to_iso8601_string())


def convert_datetime_nh1(v):
    # 2023/05/26
    # return pendulum.from_format(v, 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    dt = pendulum.from_format(v.strip(), 'YYYY/MM/DD', tz=TIMEZONE)
    return datetime.datetime.fromisoformat(dt.to_iso8601_string())


datetime_converters = {
    'kb1': convert_datetime_kb1,
    'nh1': convert_datetime_nh1
}


def read_account_info(fn: Path, ac) -> TransactionData:
    book = xlrd.open_workbook(fn)
    account_number_value = book.sheet_by_index(0).cell(ac['number_pos'][0], ac['number_pos'][1]).value
    account_name_value = book.sheet_by_index(0).cell(ac['name_pos'][0], ac['name_pos'][1]).value
    account_number = None
    account_name = None
    bank_name = ac['bank_name']
    alias = fn.with_suffix('').name
    m = re.match(ac['number_regexp'], account_number_value)
    if m:
        account_number = m.group(1)

    m = re.match(ac['name_regexp'], account_name_value)
    if m:
        account_name = m.group(1)

    return TransactionData(bank_name, account_name, account_number, alias, 'Active', 'Auto-generated', pd.DataFrame())


def read_ledger(fn, ledger_type, ledger_conf: dict) -> TransactionData:
    lc = ledger_conf

    td = read_account_info(fn, lc['account'])

    kwargs = {
        'engine': lc['excel']['engine'],
        'skiprows': lc['transaction']['start_row'],
        'usecols': lc['transaction']['column_indicies']
    }

    if 'datetime_columns' in lc['transaction']:
        cvt = dict.fromkeys(lc['transaction']['datetime_columns'], datetime_converters[ledger_type])
        kwargs['converters'] = cvt

    if 'parse_date_columns' in lc['transaction'] and 'date_format' in lc['transaction']:
        kwargs['parse_dates'] = lc['transaction']['parse_date_columns']
        kwargs['date_format'] = dict.fromkeys(kwargs['parse_dates'][0], lc['transaction']['date_format'])

    df = pd.read_excel(fn, **kwargs)
    df.columns = lc['transaction']['column_names']

    td.dataframe = df

    return td


def load_transaction_data(filelist) -> list:
    trs = []
    for fn in filelist:
        print(fn)
        lt = find_ledger_type(fn.name)
        if not lt:
            warnings.warn(f'{fn.name}은 처리할 수 없는 거래내역 엑셀파일입니다.')
            continue

        td = read_ledger(fn, lt, banks_conf[lt])
        # print(td.account_name, td.account_number)
        # print(td.dataframe)
        trs.append(td)

    return trs


def find_ledger_type(fn):
    for lt in banks_conf['data']['ledger_types']:
        pat = banks_conf[lt]['excel']['name_pattern']
        m = re.match(pat, fn)
        if m:
            return lt
    return None
