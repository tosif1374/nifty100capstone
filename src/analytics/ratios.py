# src/analytics/ratios.py
import pandas as pd
import numpy as np
from .db import query_df


# ---- Return on Equity ---------------------------------------------------
def compute_roe(company_id):
    sql = """
        SELECT p.company_id, p.year,
               p.net_profit,
               (b.equity_capital + b.reserves) AS shareholders_equity,
               ROUND(
                   100.0 * p.net_profit /
                   NULLIF(b.equity_capital + b.reserves, 0),
                   2
               ) AS roe_pct
        FROM profit_and_loss p
        JOIN balance_sheet b USING (company_id, year)
        WHERE p.company_id = ?
        ORDER BY p.year
    """
    return query_df(sql, (company_id,))


# ---- Return on Capital Employed ------------------------------------------
def compute_roce(company_id: str) -> pd.DataFrame:
    """
    ROCE = EBIT / Capital Employed
    EBIT = operating_profit + other_income - depreciation (approx)
    Capital Employed = total_assets - other_liabilities (current liabilities proxy)
    """
    sql = """
        SELECT p.company_id, p.year,
               (p.operating_profit + p.other_income - p.depreciation) AS ebit,
               (b.total_assets - b.other_liabilities) AS cap_employed,
               ROUND(
                   100.0 * (p.operating_profit + p.other_income - p.depreciation)
                   / NULLIF(b.total_assets - b.other_liabilities, 0),
                   2) AS roce_pct
        FROM profit_and_loss p
        JOIN balance_sheet b USING (company_id, year)
        WHERE p.company_id = ?
        ORDER BY p.year
    """
    return query_df(sql, (company_id,))


# ---- Debt-to-Equity -------------------------------------------------------
def compute_debt_to_equity(company_id: str) -> pd.DataFrame:
    """D/E = total borrowings / (equity_capital + reserves)"""
    sql = """
        SELECT company_id, year,
               borrowings,
               (equity_capital + reserves) AS equity,
               ROUND(borrowings / NULLIF(equity_capital + reserves, 0), 2) AS de_ratio
        FROM balance_sheet
        WHERE company_id = ?
        ORDER BY year
    """
    return query_df(sql, (company_id,))


# ---- Interest Coverage -----------------------------------------------------
def compute_interest_coverage(company_id: str) -> pd.DataFrame:
    """ICR = EBIT / Interest. ICR < 1.5 is a stress signal."""
    sql = """
        SELECT company_id, year,
               (operating_profit + other_income) AS ebit,
               interest,
               ROUND(
                   (operating_profit + other_income) / NULLIF(interest, 0),
                   2) AS icr
        FROM profit_and_loss
        WHERE company_id = ?
        ORDER BY year
    """
    return query_df(sql, (company_id,))


# ---- Price-to-Book -----------------------------------------------------------
def compute_price_to_book(company_id: str) -> pd.DataFrame:
    """
    P/B = Close Price / Book Value per Share
    Book Value per Share = (equity_capital + reserves) / shares_outstanding
    Shares outstanding approximated as: equity_capital / face_value
    Uses December closing price as the year-end price proxy.
    """
    sql = """
        SELECT b.company_id, b.year,
               sp.close_price,
               (b.equity_capital + b.reserves) AS equity,
               c.face_value,
               ROUND(b.equity_capital / NULLIF(c.face_value, 0), 0) AS shares_cr,
               ROUND(
                   (b.equity_capital + b.reserves)
                   / NULLIF(
                       b.equity_capital / NULLIF(c.face_value, 0), 0),
                   2) AS book_value_per_share,
               ROUND(
                   sp.close_price
                   / NULLIF(
                       (b.equity_capital + b.reserves)
                       / NULLIF(b.equity_capital / NULLIF(c.face_value, 0), 0),
                       0),
                   2) AS pb_ratio
        FROM balance_sheet b
        JOIN companies c ON c.id = b.company_id
        JOIN (
            SELECT company_id,
                   CAST(strftime('%Y', date) AS INT) AS price_year,
                   close_price
            FROM stock_prices
            WHERE strftime('%m', date) = '12'  -- December year-end price
        ) sp ON sp.company_id = b.company_id AND sp.price_year = b.year
        WHERE b.company_id = ?
        ORDER BY b.year
    """
    return query_df(sql, (company_id,))


# ---- Batch: all ratios for one company, one DataFrame ------------------------
def compute_all_ratios(company_id: str) -> pd.DataFrame:
    """Merge ROE, ROCE, D/E, ICR into one wide DataFrame keyed by (company_id, year)."""
    roe = compute_roe(company_id)[["company_id", "year", "roe_pct"]]
    roce = compute_roce(company_id)[["company_id", "year", "roce_pct"]]
    de = compute_debt_to_equity(company_id)[["company_id", "year", "de_ratio"]]
    icr = compute_interest_coverage(company_id)[["company_id", "year", "icr"]]

    base = roe.merge(roce, on=["company_id", "year"], how="outer")
    base = base.merge(de, on=["company_id", "year"], how="outer")
    base = base.merge(icr, on=["company_id", "year"], how="outer")
    return base.sort_values("year")
from math import pow


def net_profit_margin(net_profit, sales):
    if sales == 0:
        return None
    return net_profit / sales * 100


def roe(net_profit, equity_capital, reserves):
    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return net_profit / equity * 100


def debt_to_equity(debt, equity):
    if equity <= 0:
        return None

    return debt / equity


def interest_coverage_ratio(op_profit, interest, depreciation=0):
    if interest == 0:
        return None

    return round((op_profit - depreciation * 12) / interest, 1)

def free_cash_flow(cfo, cfi):
    return cfo + cfi


def revenue_cagr(start, end, years):
    if years < 3:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"

    if start < 0 and end > 0:
        return None, "TURNAROUND"

    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"

    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    value = ((end / start) ** (1 / years) - 1) * 100

    return value, None