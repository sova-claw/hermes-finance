#!/bin/sh
set -e
# If DB has schema but no alembic_version row, stamp 0001 so upgrade only runs new migrations.
python3 - <<'EOF'
from finance_api.core.db.engine import engine
from sqlalchemy import inspect, text
with engine.connect() as conn:
    tables = inspect(engine).get_table_names()
    if "accounts" in tables and "alembic_version" not in tables:
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
        conn.commit()
        print("Stamped alembic_version = 0001")
EOF
alembic upgrade head
exec gunicorn finance_api.main:app -c gunicorn.conf.py
