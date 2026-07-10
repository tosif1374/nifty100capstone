# src/api/deps.py

import os
import sqlite3
from typing import Generator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .auth import verify_token

DB_PATH = os.getenv("DB_PATH", "./db/nifty100.db")
SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "./data/snapshots")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Create a fresh SQLite connection for every request.
    """

    conn = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    """
    Validate JWT and return payload.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    return payload


def get_snapshot_dir() -> str:
    return SNAPSHOT_DIR


DbDep = Annotated[sqlite3.Connection, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
SnapshotDir = Annotated[str, Depends(get_snapshot_dir)]