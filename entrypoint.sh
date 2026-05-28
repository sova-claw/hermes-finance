#!/bin/sh
set -e
# If schema exists but alembic_version is missing/wrong, stamp 0001 first then upgrade.
# This handles restored databases that predate alembic tracking.
alembic upgrade head || (alembic stamp 0001 && alembic upgrade head)
exec gunicorn finance_api.main:app -c gunicorn.conf.py
