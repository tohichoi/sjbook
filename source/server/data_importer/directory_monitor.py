#!/usr/bin/python

import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import banks_conf
from data_importer.database import import_transaction_data, query_count, open_database
from data_importer.transaction import load_transaction_data


class Watcher:
    DIRECTORY_TO_WATCH = "D:/Test/bitstamp/btcEur/"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def import_ledgers(path):
        p = Path(path)
        if not p.match(banks_conf['data']['rglob_pattern']):
            return {
                'result': -1,
                'number_of_inserted_records': {
                    'bankaccounts': 0,
                    'transactions': 0,
                }
            }

        conn, cur = open_database()
        db_nbad_before = query_count(cur, 'id', 'BankAccount')
        db_ntrd_before = query_count(cur, 'id', 'Transaction')

        trs = load_transaction_data([p])
        # nbad : # of inserted band account records
        # ntrd : # of inserted transaction records
        nbad, ntrd = import_transaction_data(trs)

        db_nbad_after = query_count(cur, 'id', 'BankAccount')
        db_ntrd_after = query_count(cur, 'id', 'Transaction')

        # nbad == db_nbad_after - db_nbad_before
        # ntrd == db_ntrd_after - db_ntrd_before

        return {
            'result': nbad + ntrd,
            'number_of_inserted_records' : {
                'bankaccounts': nbad,
                'transactions': ntrd,
            }
        }


    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            # print("Received created event - %s." % event.src_path)
            Handler.import_ledgers(event.src_path)

        # elif event.event_type == 'modified':
        #     # Taken any action here when a file is modified.
        #     # print("Received modified event - %s." % event.src_path)


if __name__ == '__main__':
    w = Watcher()
    w.DIRECTORY_TO_WATCH = banks_conf['data']['root']
    w.run()
