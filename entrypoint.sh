#!/bin/sh
echo "=== entrypoint start ==="
echo "DATABASE_URL prefix: $(echo $DATABASE_URL | cut -c1-30)"
echo "PORT: $PORT"
echo "Running alembic..."
alembic upgrade head && echo "=== alembic OK ===" || { echo "=== alembic FAILED ==="; exit 1; }
echo "Starting gunicorn..."
exec gunicorn finance_api.main:app -c gunicorn.conf.py
