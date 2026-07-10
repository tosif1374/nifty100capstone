import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "./db/nifty100.db")


def get_connection(db_path=None):
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(
        f"file:{db_path}?mode=ro",
        uri=True
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn


def query_df(sql: str, params=(), db_path=None):
    import pandas as pd

    if db_path is None:
        db_path = DB_PATH

    with get_connection(db_path) as conn:
        return pd.read_sql_query(
            sql,
            conn,
            params=params
        )