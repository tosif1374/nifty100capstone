# tests/integration/test_e2e.py
from fastapi.testclient import TestClient
import pytest
from src.api.main import app
from src.screener.presets import run_preset

client = TestClient(app)

def test_api_screener_consistent_with_module3():
    """AC-13: API screener must be consistent with Module 3 Python engine."""
    api_ids = {c['company_id'] for c in
               client.get('/api/v1/screener?min_roe=15&max_de=1').json()}
    m3_ids = set(run_preset('quality_compounder')['company_id'])
    # quality_compounder has extra filters (FCF>0, rev_cagr>10) beyond API params
    # so m3_ids must be a subset of api_ids
    missing = m3_ids - api_ids
    assert not missing, f'In Module 3 but missing from API: {missing}'

@pytest.mark.parametrize('ticker',['TCS','RELIANCE','HDFCBANK','INFY','SUNPHARMA'])
def test_key_tickers_have_ratios(ticker):
    r = client.get(f'/api/v1/companies/{ticker}/ratios')
    assert r.status_code == 200 and len(r.json()) >= 10

# This test catches the case where API SQL and Python screener logic diverge -
# same input, different output set.
