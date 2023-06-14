#!/bin/bash

diff -u ../../venv/lib/python3.10/site-packages/django_pivot/pivot.py ./pivot.py > pivot.py.patch
diff -u ../../venv/lib/python3.10/site-packages/django_pivot/utils.py ./utils.py > utils.py.patch
