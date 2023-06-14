#!/bin/bash

diff -u ../../venv/lib/python3.10/site-packages/pendulum/datetime.py ./datetime.py > datetime.py.patch
