# __init__.py

# >>> import config
# >>> config.path
# PosixPath('/home/realpython/config/tic_tac_toe.toml')
#
# >>> config.tic_tac_toe
# {'user': {'player_x': {'color': 'blue'}, 'player_o': {'color': 'green'}},
#  'constant': {'board_size': 3},
#  'server': {'url': 'https://tictactoe.example.com'}}

import pathlib
import tomli

pr = pathlib.Path(__file__).parent
path = pr / "banks.toml"
with path.open(mode="rb") as fp:
    banks_conf = tomli.load(fp)

path = pr / "common.toml"
with path.open(mode="rb") as fp:
    common_conf = tomli.load(fp)
