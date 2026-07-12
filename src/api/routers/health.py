# src/api/routers/health.py
import sqlite3, time
from fastapi import APIRouter, Depends
from src.api.deps import get_db
from src.api.models import HealthResponse

router = APIRouter(tags=['health'])
START = time.time()

TABLES = ['companies','profitandloss','balancesheet','cashflow',
          'financial_ratios','sectors','stock_prices','market_cap',
          'documents','peer_percentiles']

@router.get('/health', response_model=HealthResponse)
def health(db: sqlite3.Connection = Depends(get_db)):
    counts = {}
    for t in TABLES:
        try: counts[t] = db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except: counts[t] = -1
    return HealthResponse(status='ok', db_row_counts=counts,
                           uptime_seconds=round(time.time()-START,1), version='1.0.0')
