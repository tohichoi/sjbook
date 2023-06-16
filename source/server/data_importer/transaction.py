import dataclasses
import datetime
import re
from pathlib import Path

import pandas as pd
import pendulum
import xlrd

from config import banks_conf
from data_importer.common import TIMEZONE
from data_importer.common import generate_transaction_hash
from data_importer.common import normalize_name


@dataclasses.dataclass
class TransactionData:
    bank_name: str
    account_name: str
    account_number: str
    alias: str
    status: int
    note: str
    dataframe: pd.DataFrame
    filename: Path


def swap_columns(df, col1, col2):
    col_list = list(df.columns)
    x, y = col_list.index(col1), col_list.index(col2)
    col_list[y], col_list[x] = col_list[x], col_list[y]
    df = df[col_list]
    return df


def convert_datetime_kb1(v):
    # 2023.03.02 20:43:37
    # return pendulum.from_format(v, 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    dt = pendulum.from_format(v.strip(), 'YYYY.MM.DD HH:mm:ss', tz='Asia/Seoul').in_tz('UTC')
    return datetime.datetime.fromisoformat(dt.to_rfc3339_string())


def convert_datetime_nh1(v):
    # 2023/05/26
    # return pendulum.from_format(v, 'YYYY.MM.DD HH:mm:ss', tz=TIMEZONE)
    dt = pendulum.from_format(v.strip(), 'YYYY/MM/DD', tz='Asia/Seoul').in_tz('UTC')
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

    # class BankAccountBase(models.Model):
    #     ACTIVE = 1
    #     DEACTIVE = 2
    #     REVOKED = 3
    status = 1

    return TransactionData(bank_name, account_name, account_number, alias, status, 'Auto-generated', pd.DataFrame(), fn)


def verify_transaction_data(df: pd.DataFrame):
    df['datetime'] = df['datetime'].apply(lambda x: x.tz_localize('Asia/Seoul').tz_convert('UTC') if pd.isnull(x.tz) else x)

    # try:
    #     df['datetime'] = df['datetime'].apply(lambda x: x.isoformat())
    # except AttributeError as e:
    #     pass

    # transaction_id
    # bytes(str(df['datetime']), 'utf-8')
    df['transaction_id'] = pd.Series()
    df['faccount_category_id'] = pd.Series()
    df = df.apply(generate_transaction_hash, axis=1)

    df['norm_name'] = pd.Series()
    df = df.apply(normalize_transaction_name, axis=1)

    return df


def read_ledgers(fn, ledger_type, ledger_conf: dict) -> list:
    lc = ledger_conf

    td = read_account_info(fn, lc['account'])

    kwargs = {
        'engine': lc['excel']['engine'],
        'skiprows': lc['transaction']['start_row'],
        'usecols': lc['transaction']['column_indices'],
        'sheet_name': lc['excel']['sheet_name']
    }

    if 'datetime_columns' in lc['transaction']:
        cvt = dict.fromkeys(lc['transaction']['datetime_columns'], datetime_converters[ledger_type])
        kwargs['converters'] = cvt

    if 'parse_date_columns' in lc['transaction'] and 'date_format' in lc['transaction']:
        kwargs['parse_dates'] = lc['transaction']['parse_date_columns']
        kwargs['date_format'] = dict(zip(kwargs['parse_dates'][0], lc['transaction']['date_format']))

    df0 = pd.read_excel(fn, **kwargs)
    tds = []
    for k, df in df0.items():
        df.columns = lc['transaction']['column_names']
        num_columns = ['transaction_order', 'withdraw', 'saving', 'balance']
        df[num_columns] = df[num_columns].fillna(0)
        df[num_columns] = df[num_columns].astype('int64')
        td.dataframe = verify_transaction_data(df)
        tds.append(td)

    return tds


def find_ledger_type(fn):
    for lt in banks_conf['data']['ledger_types']:
        pat = banks_conf[lt]['excel']['name_pattern']
        m = re.match(pat, fn)
        if m:
            return lt
    return None


def load_transaction_data(filelist) -> list:
    trs = []

    for lt in banks_conf['data']['ledger_types']:
        print(lt)
        pat = banks_conf[lt]['excel']['path_pattern']
        for fn in filelist:
            m = re.match(pat, str(fn))
            if not m:
                # warnings.warn(f'{fn.name}은 처리할 수 없는 거래내역 엑셀파일입니다.')
                continue
            print(fn)
            tds = read_ledgers(fn, lt, banks_conf[lt])
            # print(td.account_name, td.account_number)
            # print(td.dataframe)
            trs += tds

    return trs


def normalize_transaction_name(row):
    # logic
    # 적용 순서
    #  recipient, user_name, bank_note
    #
    # null 필드가 여러개일 때
    # recipient 가 NULL 이면 bank_note 로 대체
    # bank_note 가 NULL 이면 바꾸지 않음
    patterns = banks_conf['constants']['transaction']['remove_patterns']

    ref_col = 'recipient'
    if pd.isnull(row['recipient']) and pd.isnull(row['bank_note']):
        return row
    elif pd.isnull(row['recipient']) and not pd.isnull(row['bank_note']):
        ref_col = 'bank_note'
    elif not pd.isnull(row['recipient']) and pd.isnull(row['bank_note']):
        ref_col = 'recipient'
    # else : recipient, bank_note 둘 다 있으면 recipient 사용
    # user_note 는 테스트 데이터에 나타나지 않으므로 참고 필드에서 제외

    row['norm_name'] = normalize_name(patterns, row[ref_col])

    return row
