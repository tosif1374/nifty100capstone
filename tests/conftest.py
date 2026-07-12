# tests/conftest.py
import pytest
import pytest_asyncio
import pytest, sqlite3, pandas as pd
from httpx import AsyncClient, ASGITransport

from src.api.main import app
from src.api.auth import create_access_token


@pytest.fixture(scope="session")
def valid_token() -> str:
    """JWT token for the demo 'analyst' user — valid for the whole test session."""
    return create_access_token({"sub": "analyst", "role": "read"})


@pytest.fixture(scope="session")
def auth_headers(valid_token) -> dict:
    return {"Authorization": f"Bearer {valid_token}"}


@pytest_asyncio.fixture(scope="session")
async def client():
    """Shared async httpx client connected to the FastAPI test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture(scope='session')
def db_conn():
    conn = sqlite3.connect('data/nifty100.db')
    conn.execute('PRAGMA foreign_keys = ON;')
    yield conn
    conn.close()

@pytest.fixture(scope='session')
def ratios_df(db_conn):
    return pd.read_sql('SELECT * FROM financial_ratios', db_conn)

@pytest.fixture(scope='session')
def latest_ratios(ratios_df):
    return ratios_df.sort_values('year').groupby('company_id').last().reset_index()
