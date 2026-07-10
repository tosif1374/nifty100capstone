# src/api/routers/sectors.py
import pandas as pd
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..deps import CurrentUser, SnapshotDir, DbDep
from ..schemas import SectorSummary, SectorDetail

router = APIRouter()


# ---- GET /sectors -------------------------------------------------------
@router.get("/sectors", response_model=list[SectorSummary])
async def list_sectors(
    snapshot_dir: SnapshotDir,
    _: CurrentUser,
    year: int = Query(2024, ge=2000, le=2030),
):
    """
    Cross-sector comparison table from pre-computed snapshot.
    Returns mean ROE, ROCE, D/E, and operating margin per sector
    for the specified fiscal year (default: 2024).
    """
    snap = Path(snapshot_dir) / "sector_comparison.csv"
    if not snap.exists():
            return []

    df = pd.read_csv(snap)
    # Filter by year if the snapshot covers multiple years
    if "year" in df.columns:
        df = df[df["year"] == year]

    if df.empty:
        raise HTTPException(404, f"No sector data for year {year}")

    return df.to_dict("records")


# ---- GET /sectors/{name} -----------------------------------------------------
@router.get("/sectors/{sector_name}")
async def get_sector_detail(
    sector_name: str,
    _: CurrentUser,
    year: str = Query("Mar 2024"),
):
    """
    Detailed breakdown for a single sector: all companies with their
    ROE, ROCE, D/E, operating margin, and net margin for the given year.
    Companies sorted by ROE descending.
    """
    from src.analytics.sector_analytics import compute_sector_averages

    df = compute_sector_averages(sector_name, year)
    if df.empty:
        raise HTTPException(404, f"No data for sector '{sector_name}' in year {year}")

    return {
        "sector": sector_name,
        "year": year,
        "companies": df.to_dict("records"),
    }


# ---- GET /sector-names (distinct names) -----------------------------------------------
@router.get("/sector-names", response_model=list[str])
async def list_sector_names(db: DbDep, _: CurrentUser):
    """Utility: list all distinct sector names from sector_mapping."""
    rows = db.execute(
        "SELECT DISTINCT sector FROM sector_mapping ORDER BY sector"
    ).fetchall()
    return [r["sector"] for r in rows]
