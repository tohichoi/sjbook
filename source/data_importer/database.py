import sqlite3
import warnings

import pandas as pd

from source.config import database_conf
from source.data_importer.faccount import FAccountData
from transaction import TransactionData


def open_database(fn):
    conn = sqlite3.connect(fn)
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
        return

    sql = f'insert into BankAccount ' \
          f'(bank_name, account_name, account_number, alias, status, note)' \
          f'values (?, ?, ?, ?, ?, ?);'
    cur.execute(sql, (tr.bank_name, tr.account_name, tr.account_number, tr.alias, tr.status, tr.note))


def _import_bankaccount_data(conn: sqlite3.Connection, trs):
    cur = conn.cursor()
    for tr in trs:
        _insert_bankaccount(cur, tr)
        conn.commit()


def _query_bankaccount(cur, account_number):
    result = cur.execute('select id from BankAccount where account_number = ? limit 1', (account_number,))
    value = result.fetchone()
    if value:
        return value[0]
    return None


def _query_hash(cur, h):
    result = cur.execute(f'select transaction_id from "Transaction" where transaction_id="{h}"')
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
        td.dataframe.to_sql('Transaction', conn, index=False, if_exists='append')


def _import_transaction_data(conn: sqlite3.Connection, trs):
    for tr in trs:
        _insert_transaction_data(conn, tr)
    conn.commit()


def _insert_relation(conn, trs):
    cur = conn.cursor()
    for tr in trs:
        df: pd.DataFrame = tr.dataframe
        bank_id = _query_bankaccount(cur, tr.account_number)
        df['bank_id'] = bank_id
        df.to_sql('Transaction', conn, index=False, if_exists='append')


def _import_ledger_data(conn, trs: list):
    _import_bankaccount_data(conn, trs)
    _import_transaction_data(conn, trs)


def import_transaction_data(trs: list):
    conn, cur = open_database(database_conf['sqlite']['file'])
    # create_tables(cur)
    try:
        _import_ledger_data(conn, trs)
    except sqlite3.OperationalError as e:
        if 'no such table' in e.args:
            msg = '데이터베이스가 초기화되지 않았습니다.\n'
            msg += '다음 명령을 실행한 후 다시 시도하세요.\n'
            msg += 'cd ../server\n'
            msg += 'python recreate-database.py\n'
        else:
            raise e

    conn.close()


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


def _import_faccount_data(conn, trs: list):
    for tr in trs:
        type_pk = _insert_faccounttype_data(conn, tr)
        if not type_pk:
            raise sqlite3.DataError('Error')

        _insert_faccountmajorcategory_data(conn, type_pk, tr)
        _insert_faccountminorcategory_data(conn, type_pk, tr)



def _insert_faccountminorcategory_data(conn, type_pk, tr: FAccountData):
    cur = conn.cursor()
    columns = ['FAccountMajorCategory.name', 'FAccountMinorCategory.name']
    df2 = tr.dataframe.drop_duplicates(subset=columns).sort_values(
        by=['FAccountMajorCategory.name', 'FAccountMinorCategory.name'])
    # double check major category insertion

    # 1. 중분류 record insert
    df_minor = tr.dataframe['FAccountMinorCategory.name'].drop_duplicates()
    for r in df_minor:
        try:
            sql = '''
                insert into FAccountMinorCategory values (?, ?, ?, ?)
            '''
            cur.execute(sql, [None, r, 'Auto-Generated', None])
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in e.args:
                pass

    # 2. 대분류 record insert

    # 3. FAccountMajorMinorCategoryLink 레코드 삽입

    for idx, row in df2.iterrows():
        r = row.values.tolist()
        pk_major = _query_name_value(cur, 'FAccountMajorCategory', 'name', r[0])
        if not pk_major:
            raise sqlite3.DataError('Error')
        sql = '''
            insert into FAccountMinorCategory values (?, ?, ?, ?)
        '''
        try:
            cur.execute(sql, [None, r[1], 'Auto-Generated', pk_major])
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in e.args:
                pass

    # n = len(major_categories)
    # df2 = pd.DataFrame(
    #     data={'name': major_categories, 'note': ['Auto-generated'] * n, 'account_type_id': [type_pk] * n})
    # for idx, row in df2.iterrows():
    #     sql = '''
    #         insert into FAccountMajorCategory values (?, ?, ?, ?)
    #     '''
    #     try:
    #         cur.execute(sql, [None] + row.values.tolist())
    #     except sqlite3.IntegrityError as e:
    #         if 'UNIQUE' in e.args:
    #             pass

    conn.commit()


def _insert_faccountmajorcategory_data(conn, type_pk, tr: FAccountData):
    cur = conn.cursor()
    major_categories = tr.dataframe['FAccountMajorCategory.name'].unique()
    n = len(major_categories)
    df2 = pd.DataFrame(
        data={'name': major_categories, 'note': ['Auto-generated'] * n, 'account_type_id': [type_pk] * n})
    for idx, row in df2.iterrows():
        sql = '''
            insert into FAccountMajorCategory values (?, ?, ?, ?)
        '''
        try:
            cur.execute(sql, [None] + row.values.tolist())
        except sqlite3.IntegrityError as e:
            if 'UNIQUE' in e.args:
                pass

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

    conn.close()
