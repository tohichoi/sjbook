import hashlib


def generate_transaction_hash(row):
    s = row['datetime'].isoformat()+str(row['balance'])
    row['transaction_id'] = hashlib.md5(bytes(s, 'utf-8')).hexdigest()
    return row


TIMEZONE = 'Asia/Seoul'
