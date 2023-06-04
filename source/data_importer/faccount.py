import dataclasses
import re
import warnings
from pathlib import Path

import pandas as pd

from source.config import faccount_conf
from source.data_importer.common import TIMEZONE


@dataclasses.dataclass
class FAccountData:
    faccount_type: str
    dataframe: pd.DataFrame


def read_faccount_info(fn: Path, ac) -> FAccountData:
    return FAccountData(faccount_type=ac['type'], dataframe=pd.DataFrame())


def prepare_faccount_data(df: pd.DataFrame):
    # transaction_id
    # bytes(str(df['datetime']), 'utf-8')
    # df['transaction_id'] = pd.Series()
    # df['faccount_category_id'] = pd.Series()
    # df = df.apply(generate_hash, axis=1)

    # print(df[['datetime', 'transaction_id']])
    return df


def read_faccounts(fn, faccount_conf: dict) -> list:
    lc = faccount_conf

    fd = read_faccount_info(fn, lc)

    kwargs = {
        'engine': lc['excel']['engine'],
        'skiprows': lc['transaction']['start_row'],
        'usecols': lc['transaction']['column_indices'],
        'sheet_name': lc['excel']['sheet_name']
    }

    df0 = pd.read_excel(fn, **kwargs)
    fds = []
    for k, df in df0.items():
        df.dropna(axis=0, how='any', inplace=True)
        df.columns = lc['transaction']['column_names']
        fd.dataframe = prepare_faccount_data(df)
        fds.append(fd)

    return fds


def find_faccount_type(fn):
    for lt in faccount_conf['data']['faccount_types']:
        pat = faccount_conf[lt]['excel']['name_pattern']
        m = re.match(pat, fn)
        if m:
            return lt
    return None


def load_faccount_data(filelist) -> list:
    trs = []

    for lt in faccount_conf['data']['faccount_types']:
        print(lt)
        pat = faccount_conf[lt]['excel']['name_pattern']
        for fn in filelist:
            m = re.match(pat, fn.name)
            if not m:
                continue
            print(fn)
            tds = read_faccounts(fn, faccount_conf[lt])
            # print(td.account_name, td.account_number)
            # print(td.dataframe)
            trs += tds

    return trs
