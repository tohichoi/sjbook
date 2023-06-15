#!/bin/bash

export PYTHONPATH="$HOME/Workspace/sjbook"

./import_bank_ledgers.py

./import_faccounts.py
