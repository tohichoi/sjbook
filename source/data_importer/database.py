import sqlite3
import warnings

import pandas as pd

from source.config import database_conf
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
  

def _import_data(conn, trs: list):
    _import_bankaccount_data(conn, trs)
    _import_transaction_data(conn, trs)


def import_transaction_data(trs: list):
    conn, cur = open_database(database_conf['sqlite']['file'])
    # create_tables(cur)
    try:
        _import_data(conn, trs)
    except sqlite3.OperationalError as e:
        if 'no such table' in e.args:
            msg = '데이터베이스가 초기화되지 않았습니다.\n'
            msg += '다음 명령을 실행한 후 다시 시도하세요.\n'
            msg += 'cd ../server\n'
            msg += 'py manage.py makemigrations ; py manage.py migrate\n'
        else:
            raise e

    conn.close()
