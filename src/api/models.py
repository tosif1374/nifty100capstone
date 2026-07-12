# src/api/models.py (key schemas)
from pydantic import BaseModel
from typing import Optional

class CompanySummary(BaseModel):
    id: str; company_name: str; broad_sector: str
    roe_pct: Optional[float]=None; roce_pct: Optional[float]=None

class RatioRow(BaseModel):
    company_id: str; year: str
    net_profit_margin_pct: Optional[float]=None
    return_on_equity_pct: Optional[float]=None
    return_on_capital_pct: Optional[float]=None
    debt_to_equity: Optional[float]=None
    interest_coverage: Optional[float]=None
    free_cash_flow_cr: Optional[float]=None
    revenue_cagr_5yr: Optional[float]=None
    pat_cagr_5yr: Optional[float]=None

class HealthResponse(BaseModel):
    status: str; db_row_counts: dict; uptime_seconds: float; version: str
