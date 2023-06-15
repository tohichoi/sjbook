# __init__.py
import os
# >>> import config
# >>> config.path
# PosixPath('/home/realpython/config/tic_tac_toe.toml')
#
# >>> config.tic_tac_toe
# {'user': {'player_x': {'color': 'blue'}, 'player_o': {'color': 'green'}},
#  'constant': {'board_size': 3},
#  'server': {'url': 'https://tictactoe.example.com'}}

from pathlib import Path
import tomli


if not os.getenv('SJBOOK_ROOT'):
    raise Exception('SJBOOK_ROOT environment variable not set.')


sjbook_root=Path(os.getenv('SJBOOK_ROOT'))
if not sjbook_root.is_dir() or not sjbook_root.exists():
    raise FileNotFoundError('Invalid SJBOOK_ROOT directory.')


pr = Path(__file__).parent
path = pr / "banks.toml"
with path.open(mode="rb") as fp:
    banks_conf = tomli.load(fp)
    banks_conf['data']['root'] = sjbook_root / banks_conf['data']['root']

path = pr / "database.toml"
with path.open(mode="rb") as fp:
    database_conf = tomli.load(fp)
    database_conf['sqlite']['file'] = sjbook_root / database_conf['sqlite']['file']

path = pr / "frontend.toml"
with path.open(mode="rb") as fp:
    frontend_conf = tomli.load(fp)
    frontend_conf['path']['result'] = sjbook_root / frontend_conf['path']['result']

path = pr / "backend.toml"
with path.open(mode="rb") as fp:
    backend_conf = tomli.load(fp)
    backend_conf['server']['django']['key_file'] = sjbook_root / backend_conf['server']['django']['key_file']
    backend_conf['server']['archive_file_root'] = sjbook_root / backend_conf['server']['archive_file_root']

path = pr / "faccount.toml"
with path.open(mode="rb") as fp:
    faccount_conf = tomli.load(fp)
    faccount_conf['data']['root'] = sjbook_root / faccount_conf['data']['root']
