#!/usr/bin/env python

from pathlib import Path

import pandas as pd

from src.database import import_transaction_data, open_database
from src.transaction import load_transaction_data
from config import banks_conf, database_conf, frontend_conf


def export_data(format):
    conn, cur = open_database(database_conf['sqlite']['file'])
    sql = '''
        select BA.bank_name, BA.alias, datetime, recipient, withdraw, saving, balance, user_note, bank_note, category from "Transaction"
        inner join BankAccount BA on BA.id = "Transaction".bank_id
        order by BA.bank_name, BA.alias;
    '''
    df = pd.read_sql(sql, conn)

    outdir = Path(frontend_conf['path']['result'])
    if format == 'html':
        df.to_html(outdir / Path('result.html'))
    elif format == 'excel':
        df.to_excel(outdir / Path('result.xlsx'))


def main():
    data_root = Path(banks_conf['data']['root'])
    filelist = set(data_root.rglob("*.xls"))
    trs = load_transaction_data(filelist)
    import_transaction_data(trs)
    export_data('html')
    export_data('excel')


if __name__ == '__main__':
    main()
