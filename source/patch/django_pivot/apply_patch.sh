#!/bin/bash

patch ../../venv/lib/python3.10/site-packages/django_pivot/pivot.py < pivot.py.patch
patch ../../venv/lib/python3.10/site-packages/django_pivot/utils.py < utils.py.patch

