# tests/test_api.py
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---- Health (no auth) -------------------------------------------------------
async def test_health_returns_200(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- Auth -------------------------------------------------------------------
async def test_token_valid_credentials(client):
    r = await client.post(
        "/auth/token",
        data={"username": "analyst", "password": "nifty100pass"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_token_invalid_credentials(client):
    r = await client.post(
        "/auth/token",
        data={"username": "analyst", "password": "wrongpass"},
    )
    assert r.status_code == 401


async def test_protected_route_without_token(client):
    r = await client.get("/api/v1/companies")
    assert r.status_code in (200, 401)


# ---- Companies --------------------------------------------------------------
async def test_list_companies_returns_100(client, auth_headers):
    r = await client.get("/api/v1/companies", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) > 0


async def test_list_companies_sector_filter(client, auth_headers):
    r = await client.get(
        "/api/v1/companies?sector=Information Technology",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    assert all(
        c["sector"] == "Information Technology"
        for c in data
    )


async def test_company_summary_valid_id(client, auth_headers):
    r = await client.get("/api/v1/company/ABB", headers=auth_headers)
    assert r.status_code == 200
    assert "company_id" in r.json()


async def test_company_summary_invalid_id(client, auth_headers):
    r = await client.get("/api/v1/company/INVALID", headers=auth_headers)
    assert r.status_code == 404


async def test_company_ratios(client, auth_headers):
    r = await client.get("/api/v1/company/ABB/ratios", headers=auth_headers)
    assert r.status_code == 200

    data = r.json()

    assert data["company_id"] == "ABB"
    assert isinstance(data["ratios"], list)
    assert len(data["ratios"]) > 0


async def test_company_ratios_year_filter(client, auth_headers):
    r = await client.get(
        "/api/v1/company/ABB/ratios?start_year=2022&end_year=2024",
        headers=auth_headers,
    )
    assert r.status_code == 200

    years = [
        int(str(row["year"])[-4:])
        for row in r.json()["ratios"]
    ]

    assert all(2022 <= y <= 2024 for y in years)


# ---- Financials -------------------------------------------------------------
async def test_balance_health_valid(client, auth_headers):
    r = await client.get("/api/v1/company/ABB/balance", headers=auth_headers)
    assert r.status_code == 200
    assert "de_ratio" in r.json()


async def test_cashflow_quality_valid(client, auth_headers):
    r = await client.get("/api/v1/company/ABB/cashflow", headers=auth_headers)
    assert r.status_code == 200
    assert "cfo_quality_flag" in r.json()


async def test_price_analytics_valid(client, auth_headers):
    r = await client.get("/api/v1/company/ABB/price", headers=auth_headers)
    assert r.status_code in (200, 404)


# ---- Sectors ----------------------------------------------------------------
async def test_list_sectors(client, auth_headers):
    r = await client.get("/api/v1/sectors", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) > 0


async def test_sector_detail(client, auth_headers):
    r = await client.get(
        "/api/v1/sectors/Information Technology",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert "companies" in r.json()