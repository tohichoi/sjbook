import sqlite3
import unittest

import pandas as pd

from config import database_conf
from src.transaction import TransactionData
from src.common import generate_hash


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
            "status"         text,
            "note"           text,
            CONSTRAINT "id" PRIMARY KEY ("id" AUTOINCREMENT)
        );
    '''
    cur.execute(sql)

    sql = '''
        CREATE TABLE IF NOT EXISTS "Transaction"
        (
            "id"             integer,
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
    sql = f'insert into BankAccount ' \
          f'(bank_name, account_name, account_number, alias, status, note)' \
          f'values (?, ?, ?, ?, ?, ?);'
    cur.execute(sql, (tr.bank_name, tr.account_name, tr.account_number, tr.alias, tr.status, tr.note))


def _import_bankaccount_data(conn: sqlite3.Connection, trs):
    cur = conn.cursor()
    for tr in trs:
        _insert_bankaccount(cur, tr)
    conn.commit()


def _query_hash(conn, hash):
    cur = conn.cursor()
    result = cur.execute(f'select 1 from "Transaction" where transaction_id="{hash}"')
    value = result.fetchone()
    return value[0]
    
def _insert_transaction_data(conn: sqlite3.Connection, td: TransactionData):
    # sql = f'insert into "Transaction" ' \
    #       f'(datetime, expense, balance, saving, recipient, user_note, category, handler, bank_note, bank_id)' \
    #       f'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'
    # cur.execute(sql, (tr.bank_name, tr.account_name, tr.account_number, tr.alias, tr.status, tr.note))

    # tr.dataframe.to_sql('Transaction', conn, index=False, if_exists='append')

    for row in td.dataframe.iterrows():
        hash_df = row[1]['transaction_id']
        hash_db = _query_hash(conn, row[1]['transaction_id'])
        if hash_df == hash_db:
            warning.warn(f'Duplicated transaction: {transaction_id}')


def _import_transaction_data(conn: sqlite3.Connection, trs):
    cur = conn.cursor()
    for tr in trs:
        _insert_transaction_data(conn, tr)
    conn.commit()


def _query_bankaccount(cur, account_number):
    result = cur.execute('select id from BankAccount where account_number = ? limit 1', (account_number,))
    value = result.fetchone()
    bank_id = value[0]
    return bank_id


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
    _insert_relation(conn, trs)


def import_transaction_data(trs: list):
    conn, cur = open_database(database_conf['sqlite']['file'])
    create_tables(cur)
    _import_data(conn, trs)
    conn.close()
