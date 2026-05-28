#!/bin/sh
set -e
alembic upgrade head
exec gunicorn finance_api.main:app -c gunicorn.conf.py
