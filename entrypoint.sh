#!/bin/sh
set -e
# If schema exists without alembic tracking (missing or empty alembic_version), stamp 0001.
python3 - <<'EOF'
from finance_api.core.db.engine import engine
from sqlalchemy import inspect, text

with engine.connect() as conn:
    tables = inspect(engine).get_table_names()
    if "accounts" not in tables:
        print("Fresh DB — alembic will create schema")
    else:
        if "alembic_version" not in tables:
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
            conn.commit()
        row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
        if row is None:
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
            conn.commit()
            print("Stamped alembic_version = 0001")
        else:
            print(f"alembic_version = {row[0]}")
EOF
alembic upgrade head
exec gunicorn finance_api.main:app -c gunicorn.conf.py
