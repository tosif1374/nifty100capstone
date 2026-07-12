# tests/api/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_returns_200():
    assert client.get('/api/v1/health').status_code == 200

def test_health_has_92_companies():
    data = client.get('/api/v1/health').json()
    assert data['db_row_counts']['companies'] == 92

def test_companies_list_count():
    r = client.get('/api/v1/companies')
    assert r.status_code == 200 and len(r.json()) == 92

def test_companies_sector_filter():
    data = client.get('/api/v1/companies?sector=Information+Technology').json()
    assert len(data) == 6
    assert all(c['broad_sector']=='Information Technology' for c in data)

def test_tcs_ratios_min_10_years():
    data = client.get('/api/v1/companies/TCS/ratios').json()
    assert len(data) >= 10  # AC-12

def test_invalid_ticker_404():
    assert client.get('/api/v1/companies/INVALIDXYZ/ratios').status_code == 404

def test_screener_respects_min_roe():
    data = client.get('/api/v1/screener?min_roe=15&max_de=1').json()
    assert len(data) > 0
    for c in data:
        if c['return_on_equity_pct'] is not None:
            assert c['return_on_equity_pct'] >= 15

def test_sectors_returns_11():
    assert len(client.get('/api/v1/sectors').json()) == 11  # AC-14 related

def test_portfolio_stats_has_p50():
    data = client.get('/api/v1/portfolio/stats').json()
    assert all('p50' in row for row in data)

def test_tearsheet_missing_returns_404():
    r = client.get('/api/v1/companies/NOSUCHCO/tearsheet')
    assert r.status_code == 404  # never 500

# TestClient runs the ASGI app in-process - no Uvicorn server needed. Fast and
# reliable for CI.
