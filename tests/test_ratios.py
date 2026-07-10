import sqlite3
import pandas as pd
import pytest
from unittest.mock import patch

from src.analytics.ratios import (
    compute_roe,
    compute_roce,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_all_ratios
)


@pytest.fixture(scope="module")
def seed_db(tmp_path_factory):

    db = tmp_path_factory.mktemp("data") / "test.db"

    conn = sqlite3.connect(str(db))

    conn.executescript("""
    CREATE TABLE profit_and_loss (
        company_id TEXT,
        year INTEGER,
        sales REAL,
        operating_profit REAL,
        other_income REAL,
        interest REAL,
        depreciation REAL,
        net_profit REAL
    );

    CREATE TABLE balance_sheet (
        company_id TEXT,
        year INTEGER,
        equity_capital REAL,
        reserves REAL,
        borrowings REAL,
        other_liabilities REAL,
        total_assets REAL
    );
    """)

    pnl_rows = [
        ("TEST", 2021, 1000, 200, 20, 10, 15, 120),
        ("TEST", 2022, 1200, 250, 25, 12, 18, 150),
        ("TEST", 2023, 1400, 300, 30, 15, 20, 180),
        ("TEST", 2024, 1600, 350, 35, 18, 25, 220),
    ]

    bs_rows = [
        ("TEST", 2021, 100, 500, 200, 50, 900),
        ("TEST", 2022, 100, 600, 250, 60, 1100),
        ("TEST", 2023, 100, 700, 300, 70, 1300),
        ("TEST", 2024, 100, 800, 350, 80, 1500),
    ]

    conn.executemany(
        "INSERT INTO profit_and_loss VALUES (?,?,?,?,?,?,?,?)",
        pnl_rows
    )

    conn.executemany(
        "INSERT INTO balance_sheet VALUES (?,?,?,?,?,?,?)",
        bs_rows
    )

    conn.commit()
    conn.close()

    return str(db)


DB_ENV = "src.analytics.db.DB_PATH"


def test_roe_returns_dataframe(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_roe("TEST")
        assert isinstance(df, pd.DataFrame)


def test_roe_has_expected_columns(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_roe("TEST")
        assert {
            "company_id",
            "year",
            "roe_pct"
        }.issubset(df.columns)


def test_roe_year_count(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_roe("TEST")
        assert len(df) == 4


def test_roce_returns_dataframe(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_roce("TEST")
        assert isinstance(df, pd.DataFrame)


def test_de_ratio_returns_dataframe(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_debt_to_equity("TEST")
        assert isinstance(df, pd.DataFrame)


def test_icr_returns_dataframe(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_interest_coverage("TEST")
        assert isinstance(df, pd.DataFrame)


def test_all_ratios_columns(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_all_ratios("TEST")

        for col in [
            "roe_pct",
            "roce_pct",
            "de_ratio",
            "icr"
        ]:
            assert col in df.columns


def test_all_ratios_row_count(seed_db):
    with patch(DB_ENV, seed_db):
        df = compute_all_ratios("TEST")
        assert len(df) == 4