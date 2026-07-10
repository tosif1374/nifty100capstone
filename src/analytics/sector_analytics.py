
import pandas as pd
from .db import query_df
def get_sector_peers(company_id: str) -> list[int]:
    """Return list of company_ids in the same broad sector."""

    sql = """
    SELECT s.company_id
    FROM sectors s
    WHERE s.broad_sector = (
        SELECT broad_sector
        FROM sectors
        WHERE company_id = ?
    )
    """

    df = query_df(sql, (company_id,))
    return df["company_id"].astype(str).tolist() if not df.empty else []


def compute_sector_averages(sector: str, year: str) -> pd.DataFrame:
    if isinstance(year, int):
        year = f"Mar {year}"

    elif str(year).isdigit():
        year = f"Mar {year}"

    """
    Sector-level averages for a given fiscal year.
    """

    sql = """
    SELECT
        c.id AS company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,

        ROUND(
            100.0 * p.net_profit /
            NULLIF(b.equity_capital + b.reserves, 0),
            2
        ) AS roe_pct,

        ROUND(
            100.0 *
            (p.operating_profit + p.other_income - p.depreciation) /
            NULLIF(b.total_assets - b.other_liabilities, 0),
            2
        ) AS roce_pct,

        ROUND(
            b.borrowings /
            NULLIF(b.equity_capital + b.reserves, 0),
            3
        ) AS de_ratio,

        ROUND(
            100.0 * p.operating_profit /
            NULLIF(p.sales, 0),
            2
        ) AS op_margin_pct,

        ROUND(
            100.0 * p.net_profit /
            NULLIF(p.sales, 0),
            2
        ) AS net_margin_pct

    FROM companies c

    JOIN sectors s
        ON s.company_id = c.id

    JOIN profit_and_loss p
        ON p.company_id = c.id
        AND p.year = ?

    JOIN balance_sheet b
        ON b.company_id = c.id
        AND b.year = ?

    WHERE s.broad_sector = ?

    ORDER BY roe_pct DESC
    """

    return query_df(sql, (year, year, sector))


def compute_sector_summary(sector: str, year: str) -> pd.DataFrame:
    """
    Aggregated statistics for a sector.
    """

    df = compute_sector_averages(sector, year)

    if df.empty:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            "sector": sector,
            "year": year,
            "n_companies": len(df),
            "roe_mean": round(df["roe_pct"].mean(), 2),
            "roe_median": round(df["roe_pct"].median(), 2),
            "roce_mean": round(df["roce_pct"].mean(), 2),
            "de_mean": round(df["de_ratio"].mean(), 3),
            "op_margin_mean": round(df["op_margin_pct"].mean(), 2),
        }
    ])


def compute_peer_ranking(company_id: str, year: str) -> dict:
    """
    Rank a company among peers in its sector.
    """

    sector_row = query_df(
    """
    SELECT broad_sector
    FROM sectors
    WHERE company_id = ?
    """,
    (company_id,),
)

    if sector_row.empty:
        return {
            "company_id": company_id,
            "error": "sector not found",
        }

    sector = sector_row.iloc[0]["broad_sector"]

    df = compute_sector_averages(sector, year)

    if df.empty:
        return {
            "company_id": company_id,
            "error": "no sector data",
        }

    df = df.sort_values(
        "roe_pct",
        ascending=False
    ).reset_index(drop=True)

    df["roe_rank"] = df.index + 1

    row = df[df["company_id"] == company_id]

    if row.empty:
        return {
            "company_id": company_id,
            "error": "company not found",
        }

    r = row.iloc[0]
    n = len(df)

    return {
        "company_id": company_id,
        "sector": sector,
        "year": year,
        "n_peers": n,
        "roe_pct": r["roe_pct"],
        "roe_rank": int(r["roe_rank"]),
        "roe_percentile": round(
            (1 - ((int(r["roe_rank"]) - 1) / n)) * 100,
            1,
        ),
        "roce_pct": r["roce_pct"],
        "op_margin_pct": r["op_margin_pct"],
    }


def compute_all_sectors_latest(latest_year: str = "2024") -> pd.DataFrame:
    """
    Cross-sector comparison table.
    """

    sectors = query_df(
        """
        SELECT DISTINCT broad_sector
        FROM sectors
        ORDER BY broad_sector
        """
    )

    frames = []

    for sector in sectors["broad_sector"].tolist():
        summary = compute_sector_summary(
            sector,
            latest_year,
        )

        if not summary.empty:
            frames.append(summary)

    return (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame()
    )