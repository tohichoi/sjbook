#!/usr/bin/env python

from pathlib import Path

import pandas as pd

from database import import_transaction_data, open_database
from transaction import load_transaction_data
from config import banks_conf, database_conf, frontend_conf
import argparse


def export_data(file_format):
    conn, cur = open_database(database_conf['sqlite']['file'])
    sql = '''
        select BA.bank_name, BA.alias, datetime, recipient, withdraw, saving, balance, user_note, bank_note, category 
            from "Transaction"
        inner join BankAccount BA on BA.id = "Transaction".bank_id
        order by BA.bank_name, BA.alias;
    '''
    df = pd.read_sql(sql, conn)

    output_dir = Path(frontend_conf['path']['result'])
    if file_format == 'html':
        df.to_html(output_dir / Path('result.html'))
    elif file_format == 'excel':
        df.to_excel(output_dir / Path('result.xlsx'))


def main():
    parser = argparse.ArgumentParser('Importing ledgers')
    parser.add_argument('--data-root', type=str)
    args = parser.parse_args()

    data_root = Path(banks_conf['data']['root']) if not args.data_root else Path(args.data_root)
    if not data_root.exists():
        raise FileNotFoundError(f'{data_root} not found')
    filelist = set(data_root.rglob(banks_conf['data']['rglob_pattern']))
    trs = load_transaction_data(filelist)
    import_transaction_data(trs)
    # export_data('html')
    # export_data('excel')


if __name__ == '__main__':
    main()
