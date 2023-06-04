#!/usr/bin/env python

from pathlib import Path

import pandas as pd

from database import import_transaction_data, open_database, import_faccount_data
from source.data_importer.faccount import load_faccount_data
from transaction import load_transaction_data
from source.config import banks_conf, database_conf, frontend_conf, faccount_conf


def export_data(file_format):
    # conn, cur = open_database(database_conf['sqlite']['file'])
    # sql = '''
    #     select BA.bank_name, BA.alias, datetime, recipient, withdraw, saving, balance, user_note, bank_note, category
    #         from "Transaction"
    #     inner join BankAccount BA on BA.id = "Transaction".bank_id
    #     order by BA.bank_name, BA.alias;
    # '''
    # df = pd.read_sql(sql, conn)
    #
    # output_dir = Path(frontend_conf['path']['result'])
    # if file_format == 'html':
    #     df.to_html(output_dir / Path('result.html'))
    # elif file_format == 'excel':
    #     df.to_excel(output_dir / Path('result.xlsx'))
    pass


def main():
    data_root = Path(faccount_conf['data']['root'])
    filelist = set(data_root.rglob("*.xls*"))
    trs = load_faccount_data(sorted(filelist))
    import_faccount_data(trs)
    # import_faccount_data(trs)
    # export_data('html')
    # export_data('excel')


if __name__ == '__main__':
    main()
