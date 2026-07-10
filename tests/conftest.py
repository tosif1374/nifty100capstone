# tests/conftest.py
import pytest
import pytest_asyncio
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
