# src/analytics/pnl_trends.py

import pandas as pd
import numpy as np
import re
from .db import query_df


def cagr(start_value: float, end_value: float, n_years: int) -> float | None:
    """
    Compound Annual Growth Rate.
    Formula: (end/start)^(1/n) - 1
    """
    if (
        n_years < 1
        or start_value is None
        or end_value is None
        or start_value <= 0
        or end_value <= 0
    ):
        return None

    return round((end_value / start_value) ** (1 / n_years) - 1, 4)


def extract_year(value):
    """
    Extracts 4-digit year from values like:
    'Mar 2020', 'Sep 2024', '2023'

    Returns:
        int | None
    """
    if pd.isna(value):
        return None

    match = re.search(r"(\d{4})", str(value))
    return int(match.group(1)) if match else None


def _pnl(company_id: str) -> pd.DataFrame:
    """Fetch full P&L ordered by year."""
    return query_df(
        """
        SELECT *
        FROM profit_and_loss
        WHERE company_id = ?
        ORDER BY year
        """,
        (company_id,),
    )


def compute_sales_cagr(company_id: str, years: int = 5) -> dict:
    """
    Sales CAGR over most recent N years.
    """
    df = _pnl(company_id).dropna(subset=["sales"])

    if len(df) < 2:
        return {}

    df = df.tail(years + 1)

    start_year = extract_year(df.iloc[0]["year"])
    end_year = extract_year(df.iloc[-1]["year"])

    n = len(df) - 1

    return {
        "company_id": company_id,
        "years": n,
        "start_year": start_year,
        "end_year": end_year,
        "start_sales": float(df.iloc[0]["sales"]),
        "end_sales": float(df.iloc[-1]["sales"]),
        "sales_cagr": cagr(
            float(df.iloc[0]["sales"]),
            float(df.iloc[-1]["sales"]),
            n,
        ),
    }


def compute_profit_cagr(company_id: str, years: int = 5) -> dict:
    """
    Net Profit CAGR.
    """
    df = _pnl(company_id).dropna(subset=["net_profit"])

    if len(df) < 2:
        return {}

    df = df.tail(years + 1)

    start_year = extract_year(df.iloc[0]["year"])
    end_year = extract_year(df.iloc[-1]["year"])

    n = len(df) - 1

    return {
        "company_id": company_id,
        "years": n,
        "start_year": start_year,
        "end_year": end_year,
        "start_profit": float(df.iloc[0]["net_profit"]),
        "end_profit": float(df.iloc[-1]["net_profit"]),
        "profit_cagr": cagr(
            float(df.iloc[0]["net_profit"]),
            float(df.iloc[-1]["net_profit"]),
            n,
        ),
    }


def compute_margin_series(company_id: str) -> pd.DataFrame:
    sql = """
        SELECT
            company_id,
            year,
            sales,
            operating_profit,
            net_profit,
            depreciation,

            ROUND(
                100.0 * operating_profit / NULLIF(sales,0),
                2
            ) AS operating_margin,

            ROUND(
                100.0 * net_profit / NULLIF(sales,0),
                2
            ) AS net_margin,

            ROUND(
                100.0 * (operating_profit + depreciation)
                / NULLIF(sales,0),
                2
            ) AS ebitda_margin

        FROM profit_and_loss
        WHERE company_id = ?
        ORDER BY year
    """

    return query_df(sql, (company_id,))


def compute_eps_trend(company_id: str) -> pd.DataFrame:
    sql = """
        SELECT
            p.company_id,
            p.year,
            p.eps,
            p.net_profit,

            ROUND(
                b.equity_capital /
                NULLIF(c.face_value,0),
                0
            ) AS shares_cr,

            ROUND(
                p.net_profit /
                NULLIF(
                    b.equity_capital /
                    NULLIF(c.face_value,0),
                    0
                ),
                2
            ) AS eps_computed

        FROM profit_and_loss p
        JOIN balance_sheet b
            USING(company_id, year)
        JOIN companies c
            ON c.id = p.company_id

        WHERE p.company_id = ?
        ORDER BY p.year
    """

    df = query_df(sql, (company_id,))

    if df.empty:
        return df

    df["eps_yoy_pct"] = (
        df["eps"]
        .pct_change()
        .mul(100)
        .round(2)
    )

    df["eps_unit_flag"] = (
        df["eps"].notna()
        & df["eps_computed"].notna()
        & (
            (
                df["eps"]
                / df["eps_computed"].replace(0, pd.NA)
            ).abs()
            > 10
        )
    )

    return df


def compute_dividend_stability(company_id: str) -> dict:
    df = query_df(
        """
        SELECT year, dividend_payout
        FROM profit_and_loss
        WHERE company_id = ?
        AND dividend_payout IS NOT NULL
        ORDER BY year
        """,
        (company_id,),
    )

    if df.empty:
        return {
            "company_id": company_id,
            "div_mean": None,
            "div_std": None,
            "div_cv": None,
        }

    mean = df["dividend_payout"].mean()
    std = df["dividend_payout"].std()

    return {
        "company_id": company_id,
        "div_years": len(df),
        "div_mean": round(float(mean), 2),
        "div_std": round(float(std), 2),
        "div_cv": round(float(std / mean), 3)
        if mean != 0
        else None,
    }