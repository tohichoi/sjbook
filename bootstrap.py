#!/usr/bin/env python

import os
import sys

import requests


PROTOCOL='http://'


def test_connection(host):
    r = requests.get(PROTOCOL+host)
    # if not r.ok:
    #     raise requests.ConnectionError(f'Cannot connect to {host}')
    print(f'Connected to {host}')
    r.close()
    

def test_env(e, suggest):
    if not os.getenv(e):
        print(f"'{e}' is not set. Use the following command. \n\n{suggest}\n")
    
    
def print_env(e):
    print(f'{e}={os.getenv(e)}')
    

# root = os.getenv('SJBOOK_ROOT')
# restapi_host = os.getenv('SJBOOK_RESTAPI_HOST')
# frontend_host = os.getenv('SJBOOK_FRONTEND_HOST')

# if not root:
#     raise EnvironmentError("'SJBOOK_ROOT' is not set. Use the following command. \n\nexport SJBOOK_ROOT=$(pwd)")

# if not restapi_host:
#     raise EnvironmentError("'SJBOOK_RESTAPI_HOST' is not set. Use the following command. \n\nexport SJBOOK_RESTAPI_HOST=localhost:8000")

# if not frontend_host:
#     raise EnvironmentError("'SJBOOK_FRONTEND_HOST' is not set. Use the following command. \n\nexport SJBOOK_FRONTEND_HOST=localhost:8001")


print('* Environment tests')
envs = ('SJBOOK_ROOT', 'SJBOOK_RESTAPI_HOST', 'SJBOOK_FRONTEND_HOST')
suggests = (
'export SJBOOK_ROOT=$(pwd)', 'export SJBOOK_RESTAPI_HOST=localhost:8000', 'export SJBOOK_FRONTEND_HOST=localhost:8001')
is_env_set = []
for e, s in (zip(envs, suggests)):
    is_env_set.append(os.environ.get(e, None))

print('* Environment variables')
for e in envs:
    print_env(e)

for i in range(len(is_env_set)):
    if not is_env_set[i]:
        print(suggests[i])


# print(f'SJBOOK_ROOT={os.getenv()}')
# print(f'SJBOOK_RESTAPI_HOST={restapi_host}')
# print(f'SJBOOK_FRONTEND_HOST={frontend_host}')
# print()
# print('Connection tests')
# for h in [restapi_host, frontend_host]:
#     test_connection(h)

try:
    r = input('Press ENTER or SPACE to continue ... ')
except EOFError:
    sys.exit(1)

sys.exit(0)