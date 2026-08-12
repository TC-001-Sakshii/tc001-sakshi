import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    base_dir = Path(__file__).resolve().parent.parent
    schema = (base_dir / "schema.sql").read_text(encoding="utf-8")
    seed = (base_dir / "seed.sql").read_text(encoding="utf-8")
    db.executescript(schema)
    db.executescript(seed)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
