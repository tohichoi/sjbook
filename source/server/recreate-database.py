#!/usr/bin/env python
from pathlib import Path
import shutil
from config import database_conf

# delete database file
fn = database_conf['sqlite']['file']
Path(fn).unlink(missing_ok=True)

# delete migrations directory
shutil.rmtree(Path('restful_server/migrations'))
