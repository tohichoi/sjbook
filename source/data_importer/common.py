import copy
import hashlib
import re


# TIMEZONE = 'Asia/Seoul'
TIMEZONE = 'UTC'


def generate_transaction_hash(row):
    s = row['datetime'].isoformat() + str(row['balance'])
    row['transaction_id'] = hashlib.md5(bytes(s, 'utf-8')).hexdigest()
    return row


def normalize_name(remove_patterns, core_name):
    # 숫자 제거
    # ㈜
    norm_name = copy.copy(core_name)
    try:
        noise = remove_patterns
        for n_p, n_r in noise:
            norm_name = re.sub(n_p, n_r, norm_name)

        if len(norm_name) < 2:
            norm_name = core_name

        return norm_name
    except TypeError:
        return core_name
