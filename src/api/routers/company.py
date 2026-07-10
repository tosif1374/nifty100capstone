# src/api/routers/company.py
import json
import pandas as pd
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..deps import DbDep, CurrentUser, SnapshotDir
from ..schemas import (
    CompanyList, RatiosResponse, RatioYear,
    PnLResponse, CAGRSummary, MarginYear,
)

router = APIRouter()


# ---- GET /companies -------------------------------------------------------
@router.get("/companies", response_model=list[CompanyList])
async def list_companies(
    db: DbDep,
    _: CurrentUser,
    sector: str | None = Query(None, description="Filter by sector name"),
):
    """List all Nifty 100 companies with optional sector filter."""
    sql = """
        SELECT c.id, c.company_name, c.website,
               s.sector, s.industry
        FROM companies c
        LEFT JOIN sector_mapping s ON s.company_id = c.id
    """
    params = []
    if sector:
        sql += " WHERE s.sector = ?"
        params.append(sector)
    sql += " ORDER BY c.id"

    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ---- GET /company/{id} -----------------------------------------------------
@router.get("/company/{company_id}")
async def get_company_summary(
    company_id: str,
    snapshot_dir: SnapshotDir,
    _: CurrentUser,
    live: bool = Query(False, description="Use live analytics instead of snapshot"),
):
    """
    Full company summary.
    Default (live=false): reads from data/snapshots/company_summary.json.
    With ?live=true: calls compute_all_ratios + all summary functions in real time.
    """
    if not live:
        snap = Path(snapshot_dir) / "company_summary.json"

        if not snap.exists():
            live = True
        else:
            data = json.loads(snap.read_text())

            company = data.get(str(company_id))

            if company is None:
                raise HTTPException(
                    404,
                    f"company_id {company_id} not found in snapshot"
                )

        return company



    # Live mode
    from src.analytics.ratios import compute_all_ratios
    from src.analytics.pnl_trends import compute_sales_cagr, compute_profit_cagr
    from src.analytics.balance_health import compute_balance_health_summary
    from src.analytics.cashflow_quality import compute_cashflow_summary
    from src.analytics.price_analytics import compute_price_summary
    from src.analytics.sector_analytics import compute_peer_ranking

    return {
        "company_id": company_id,
        "latest_ratios": compute_all_ratios(company_id).tail(1).to_dict("records"),
        "sales_cagr_5yr": compute_sales_cagr(company_id, 5).get("sales_cagr"),
        "balance_health": compute_balance_health_summary(company_id),
        "cashflow": compute_cashflow_summary(company_id),
        "price": compute_price_summary(company_id),
        "peer_ranking": compute_peer_ranking(company_id, 2024),
    }


# ---- GET /company/{id}/ratios -----------------------------------------------
@router.get("/company/{company_id}/ratios", response_model=RatiosResponse)
async def get_company_ratios(
    company_id: str,
    _: CurrentUser,
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
):
    """ROE, ROCE, D/E, ICR per year. Optional year range filter."""
    from src.analytics.ratios import compute_all_ratios

    df = compute_all_ratios(company_id)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No ratio data for company_id {company_id}",
        )

    # Extract numeric year for filtering
    df["year_num"] = pd.to_numeric(
        df["year"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    df = df.dropna(subset=["year_num"])
    df["year_num"] = df["year_num"].astype(int)

    # Apply filters
    if start_year is not None:
        df = df[df["year_num"] >= start_year]

    if end_year is not None:
        df = df[df["year_num"] <= end_year]

    # Remove helper column before response
    df = df.drop(columns=["year_num"])

    return RatiosResponse(
        company_id=company_id,
        ratios=[
            RatioYear(**row)
            for row in df.to_dict(orient="records")
        ],
    )


# ---- GET /company/{id}/pnl ---------------------------------------------------
@router.get("/company/{company_id}/pnl", response_model=PnLResponse)
async def get_company_pnl(
    company_id: str,
    _: CurrentUser,
    cagr_years: int = Query(5, ge=1, le=10),
):
    """P&L trends: sales/profit CAGR, margin series, EPS unit flag count."""
    from src.analytics.pnl_trends import (
        compute_sales_cagr, compute_profit_cagr,
        compute_margin_series, compute_eps_trend,
    )

    margins = compute_margin_series(company_id)
    eps_df = compute_eps_trend(company_id)
    sc = compute_sales_cagr(company_id, cagr_years)
    pc = compute_profit_cagr(company_id, cagr_years)

    def _cagr_summary(d, val_key_start, val_key_end, cagr_key):
        if not d:
            return None
        return CAGRSummary(
            years=d["years"], start_year=d["start_year"], end_year=d["end_year"],
            start_value=d[val_key_start], end_value=d[val_key_end],
            cagr=d.get(cagr_key),
        )

    return PnLResponse(
        company_id=company_id,
        sales_cagr=_cagr_summary(sc, "start_sales", "end_sales", "sales_cagr"),
        profit_cagr=_cagr_summary(pc, "start_profit", "end_profit", "profit_cagr"),
        margin_series=[
            MarginYear(**r) for r in
            margins[["year", "operating_margin", "net_margin", "ebitda_margin"]]
            .to_dict("records")
        ],
        eps_unit_flags=int(eps_df["eps_unit_flag"].sum()) if not eps_df.empty else 0,
    )
