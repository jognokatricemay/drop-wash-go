"""MySQL connection and small query helpers.

Use these instead of opening connections yourself:
    rows = query("SELECT * FROM shops")                       # list of dicts
    shop = query("SELECT * FROM shops WHERE id=%s", [1], one=True)
    new_id = execute("INSERT INTO ... VALUES (%s, %s)", [a, b])
Always pass values as the second argument (never build SQL with f-strings),
so user input can't break the query (SQL injection).
"""
from pathlib import Path

import click
import pymysql
from flask import current_app, g


def connect(with_db=True):
    cfg = current_app.config
    return pymysql.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"] if with_db else None,
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
        autocommit=False,
    )


def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=None, one=False):
    with get_db().cursor() as cur:
        cur.execute(sql, args or [])
        rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=None):
    """Run INSERT/UPDATE/DELETE and save it. Returns the new row id for INSERTs."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, args or [])
        new_id = cur.lastrowid
    db.commit()
    return new_id


@click.command("init-db")
def init_db_command():
    """Create the database and tables, then add the sample data."""
    from .seed import seed

    close_db()  # an open connection would block DROP TABLE
    name = current_app.config["DB_NAME"]
    conn = connect(with_db=False)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"USE `{name}`")
        schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
        schema = "\n".join(line for line in schema.splitlines() if not line.strip().startswith("--"))
        for statement in [s.strip() for s in schema.split(";") if s.strip()]:
            cur.execute(statement)
    conn.commit()
    conn.close()
    seed()
    click.echo(f"Database '{name}' is ready with sample data.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
