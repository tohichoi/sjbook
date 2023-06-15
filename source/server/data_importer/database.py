import sqlite3
import warnings

import pandas as pd

from data_importer.common import normalize_name
from config import database_conf
from data_importer.faccount import FAccountData
from data_importer.transaction import TransactionData


def open_database(fn=None):
    f = fn
    if not fn:
        f = database_conf['sqlite']['file']
    conn = sqlite3.connect(f)
    return conn, conn.cursor()
    # return conn


def create_tables(cur):
    sql = '''
        CREATE TABLE IF NOT EXISTS "BankAccount"
        (
            "id"             integer,
            "bank_name"      TEXT NOT NULL,
            "account_name"   TEXT NOT NULL,
            "account_number" text NOT NULL,
            "alias"          text,
            "status"         integer,
            "note"           text,
            CONSTRAINT "id" PRIMARY KEY ("id" AUTOINCREMENT)
        );
    '''
    cur.execute(sql)

    sql = '''
        CREATE TABLE IF NOT EXISTS "Transaction"
        (
            "id"             integer,
            "transaction_order" int NOT NULL,
            "datetime"       TEXT NOT NULL,
            "withdraw"        int DEFAULT 0,
            "balance"        int DEFAULT 0,
            "saving"         int DEFAULT 0,
            "recipient"      text,
            "user_note"      text,
            "category"       text,
            "handler"        text,
            "bank_note"      text,
            "transaction_id" text,
            "bank_id"        int NOT NULL,
            FOREIGN KEY (bank_id) REFERENCES BankAccount(id),
            CONSTRAINT "id" PRIMARY KEY ("id" AUTOINCREMENT)
        );
    '''
    cur.execute(sql)
    # create_simple_table(conn, table_name, columns)


def _insert_bankaccount(cur: sqlite3.Cursor, tr: TransactionData):
    bank_id = _query_bankaccount(cur, tr.account_number)
    if bank_id:
        warnings.warn(f'{tr.bank_name}:{tr.alias}:{tr.account_number} exists')
        return 0

    sql = f'insert into BankAccount ' \
          f'(bank_name, account_name, account_number, alias, status, note)' \
          f'values (?, ?, ?, ?, ?, ?);'
    cur.execute(sql, (tr.bank_name, tr.account_name, tr.account_number, tr.alias, tr.status, tr.note))
    return 1


def _import_bankaccount_data(conn: sqlite3.Connection, trs):
    cur = conn.cursor()
    n = 0
    for tr in trs:
        n += _insert_bankaccount(cur, tr)
        conn.commit()
    return n


def _query_bankaccount(cur, account_number):
    result = cur.execute('select id from BankAccount where account_number = ? limit 1', (account_number,))
    value = result.fetchone()
    if value:
        return value[0]
    return None


def query_count(cur, count_field, table_name):
    result = cur.execute('select count({}) from {}'.format(count_field, f'"{table_name}"'))
    value = result.fetchone()
    if value:
        return value[0]
    return None


def _query_hash(cur, h):
    result = cur.execute('select transaction_id from "Transaction" where transaction_id=?', (h,))
    value = result.fetchone()
    if value:
        return value[0]
    return None


def _insert_transaction_data(conn: sqlite3.Connection, td: TransactionData):
    cur = conn.cursor()
    bank_id = _query_bankaccount(cur, td.account_number)
    td.dataframe['bank_id'] = bank_id

    dup_record_iloc = []
    nrecords = td.dataframe.shape[0]
    for idx, row in td.dataframe.iterrows():
        hash_df = row['transaction_id']
        hash_db = _query_hash(cur, row['transaction_id'])
        if hash_df == hash_db:
            # warnings.warn(f'Duplicated transaction: {hash_db}')
            dup_record_iloc.append(idx)

    if len(dup_record_iloc) > 0:
        td.dataframe = td.dataframe.drop(dup_record_iloc)
        warnings.warn(f'{td.bank_name} : {len(dup_record_iloc)} / {nrecords} transactions dropped')

    if td.dataframe.shape[0] > 0:
        # td.dataframe['datetime'] = td.dataframe['datetime'].apply(lambda x: x.tz_convert('UTC'))
        datetime_format = None
        # if database_conf['database']['engine'] == 'sqlite':
        #     warnings.warn('SQLite does not support timezone-aware datetime. Data saved as UTC time.')
        #     # YYYY-MM-DDTHH:MM:SS
        #     # sqlite : https://www.sqlite.org/lang_datefunc.html
        #     # python : https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
        #     datetime_format = '%Y-%m-%dT%H:%M:%S'
        td.dataframe['datetime'] = td.dataframe['datetime'].apply(lambda x: x.isoformat())
        td.dataframe.to_sql('Transaction', conn, index=False, if_exists='append')

    return td.dataframe.shape[0]


def _import_transaction_data(conn: sqlite3.Connection, trs):
    n = 0
    for tr in trs:
        n += _insert_transaction_data(conn, tr)
    conn.commit()
    return n


def _insert_relation(conn, trs):
    cur = conn.cursor()
    for tr in trs:
        df: pd.DataFrame = tr.dataframe
        bank_id = _query_bankaccount(cur, tr.account_number)
        df['bank_id'] = bank_id
        df.to_sql('Transaction', conn, index=False, if_exists='append')


def _import_ledger_data(conn, trs: list):
    nbad = _import_bankaccount_data(conn, trs)
    ntrd = _import_transaction_data(conn, trs)

    return nbad, ntrd


def import_transaction_data(trs: list):
    conn, cur = open_database(database_conf['sqlite']['file'])
    # create_tables(cur)
    try:
        nbad, ntrd = _import_ledger_data(conn, trs)
        conn.close()
        return nbad, ntrd

    except sqlite3.OperationalError as e:
        if 'no such table' in e.args:
            msg = '데이터베이스가 초기화되지 않았습니다.\n'
            msg += '다음 명령을 실행한 후 다시 시도하세요.\n'
            msg += 'cd ../server\n'
            msg += 'python recreate-database.py\n'
        else:
            raise e

def _query_name_value(cur, table_name, column_name, value):
    result = cur.execute(f'select id from {table_name} where {column_name} = ? limit 1', (value,))
    value = result.fetchone()
    if value:
        return value[0]
    return None


def _query_faccounttype(cur, faccount_type):
    return _query_name_value(cur, 'FAccountCategoryType', 'name', faccount_type)


def _insert_faccounttype_data(conn, tr):
    # FAccountType
    cur = conn.cursor()
    sql = '''
        insert into FAccountCategoryType values (?, ?, ?)
    '''
    try:
        cur.execute(sql, (None, tr.faccount_type, 'Auto-generated'))
        conn.commit()
    except sqlite3.IntegrityError as e:
        if 'UNIQUE' in e.args:
            pass

    return _query_name_value(cur, 'FAccountCategoryType', 'name', tr.faccount_type)


def _insert_faccountsubcategory_data(conn, type_pk, tr):
    pass


def _insert_faccountcategory_data(conn, type_pk, tr):
    cur = conn.cursor()
    columns = ['FAccountCategory.name']
    df2 = tr.dataframe.drop_duplicates(subset=columns).sort_values(
        by=['FAccountCategory.name'])
    df2.columns = ['major', 'minor', 'core', 'norm_name']
    for idx, row in df2.iterrows():
        try:
            minor_pk = _query_name_value(cur, 'FAccountMinorCategory', 'name', row['minor'])
            if not minor_pk:
                raise Exception(f'Cannot find {row["minor_pk"]} in FAccountMinorCategory')
            # norm_name = normalize_name(row['core'])
            sql = '''
                insert into FAccountCategory values (?, ?, ?, ?, ?)
            '''
            cur.execute(sql, [None, row['core'], row['norm_name'], 'Auto-Generated', minor_pk])
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in str(e):
                pass
            else:
                raise e


def _import_faccount_data(conn, trs: list):
    for tr in trs:
        type_pk = _insert_faccounttype_data(conn, tr)
        if not type_pk:
            raise sqlite3.DataError('Error')

        _insert_faccountmajorcategory_data(conn, type_pk, tr)
        _insert_faccountminorcategory_data(conn, type_pk, tr)
        _insert_faccountcategory_data(conn, type_pk, tr)


def _insert_faccountminorcategory_data(conn, type_pk, tr: FAccountData):
    cur = conn.cursor()
    columns = ['FAccountMajorCategory.name', 'FAccountMinorCategory.name']
    df2 = tr.dataframe.drop_duplicates(subset=columns).sort_values(
        by=['FAccountMajorCategory.name', 'FAccountMinorCategory.name'])
    df2.columns = ['major', 'minor', 'core', 'norm_name']
    # double check major category insertion

    for idx, row in df2.iterrows():
        try:
            # major_pk = _query_name_value(cur, 'FAccountMajorCategory', 'name', row['major'])
            # if not major_pk:
            #     raise Exception(f'Cannot find {row["major"]} in FAccountMajorCategory')
            # _insert_faccountmajorcategory_record(cur, [r['major'], 'Auto-generated', type_pk])
            sql = '''
                insert into FAccountMinorCategory values (?, ?, ?)
            '''
            cur.execute(sql, [None, row['minor'], 'Auto-Generated'])
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in str(e):
                pass
            else:
                raise e

    for idx, row in df2.iterrows():
        try:
            major_pk = _query_name_value(cur, 'FAccountMajorCategory', 'name', row['major'])
            if not major_pk:
                raise Exception(f'Cannot find {row["major"]} in FAccountMajorCategory')
            minor_pk = _query_name_value(cur, 'FAccountMinorCategory', 'name', row['minor'])
            if not minor_pk:
                raise Exception(f'Cannot find {row["minor_pk"]} in FAccountMinorCategory')

            r = cur.execute('''
                select 1 from FAccountMajorMinorCategoryLink where
                    major_category_id = ? and minor_category_id = ?
            ''', (major_pk, minor_pk))
            result = r.fetchone()
            if result:
                continue

            sql = '''
                insert into FAccountMajorMinorCategoryLink values (?, ?, ?)
            '''
            cur.execute(sql, [None, major_pk, minor_pk])
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in str(e):
                pass
            else:
                raise e

    conn.commit()


def _insert_faccountmajorcategory_record(cur, values: list):
    sql = '''
        insert into FAccountMajorCategory values (?, ?, ?, ?)
    '''
    try:
        r = cur.execute(sql, [None] + values)
        if r:
            result = r.fetchone()
    except sqlite3.IntegrityError as e:
        if 'UNIQUE' in str(e):
            pass
    except sqlite3.InterfaceError as e2:
        print(e2)


def _insert_faccountmajorcategory_data(conn, type_pk, tr: FAccountData):
    cur = conn.cursor()
    df2 = tr.dataframe[['FAccountMajorCategory.name', ]].drop_duplicates()
    for idx, row in df2.iterrows():
        _insert_faccountmajorcategory_record(cur, [row['FAccountMajorCategory.name'], 'Auto-generated', type_pk])

    conn.commit()


def import_faccount_data(trs: list):
    conn, cur = open_database(database_conf['sqlite']['file'])
    # create_tables(cur)
    try:
        _import_faccount_data(conn, trs)
    except sqlite3.OperationalError as e:
        if 'no such table' in e.args:
            msg = '데이터베이스가 초기화되지 않았습니다.\n'
            msg += '다음 명령을 실행한 후 다시 시도하세요.\n'
            msg += 'cd ../server\n'
            msg += 'python recreate-database.py\n'
        else:
            raise e
    except sqlite3.InterfaceError as e:
        print(e)

    conn.close()
