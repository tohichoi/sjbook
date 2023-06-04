#!/usr/bin/env python
import subprocess
from pathlib import Path
import shutil
from config import database_conf

# delete database file
f = Path(database_conf['sqlite']['file'])
f.unlink(missing_ok=True)
if f.exists():
    raise FileExistsError('Cannot delete file')

# delete migrations directory
try:
    shutil.rmtree(Path('restful_server/migrations'))
except FileNotFoundError:
    pass

# make migrations
cmds = [
    'python manage.py makemigrations',
    'python manage.py migrate',
    'python manage.py makemigrations restful_server',
    'python manage.py migrate restful_server',
]

for cmd in cmds:
    subprocess.run(cmd, shell=True)