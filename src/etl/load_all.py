import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = "db/nifty100.db"
DATA_PATH = Path("data/clean")


FILES = {
    "companies .xlsx": "companies",
    "profitandloss.xlsx": "profit_and_loss",
    "balancesheet.xlsx": "balance_sheet",
    "cashflow.xlsx": "cash_flow",
    "financial_ratios.xlsx": "financial_ratios",
    "market_cap.xlsx": "market_cap",
    "sectors.xlsx": "sectors",
    "peer_groups.xlsx": "peer_groups",
    "stock_prices.xlsx": "stock_prices",
    "documents.xlsx": "documents",
    "analysis.xlsx": "analysis",
    "prosandcons.xlsx": "pros_and_cons"
}


def create_audit_table(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS load_audit(
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TEXT,
        file_name TEXT,
        rows_attempted INTEGER,
        rows_loaded INTEGER,
        rows_rejected INTEGER,
        notes TEXT
    )
    """)
    conn.commit()


def record_audit(
    conn,
    file_name,
    rows_attempted,
    rows_loaded,
    notes=""
):
    conn.execute(
        """
        INSERT INTO load_audit(
            run_timestamp,
            file_name,
            rows_attempted,
            rows_loaded,
            rows_rejected,
            notes
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            datetime.now().isoformat(),
            file_name,
            rows_attempted,
            rows_loaded,
            rows_attempted - rows_loaded,
            notes
        )
    )
    conn.commit()


conn = sqlite3.connect(DB_PATH)

create_audit_table(conn)

for file_name, table_name in FILES.items():

    path = DATA_PATH / file_name

    df = pd.read_excel(path)

    attempted = len(df)

    before = conn.total_changes

    df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False
    )

    loaded = conn.total_changes - before

    record_audit(
        conn,
        file_name,
        attempted,
        loaded
    )

    print(
        f"{file_name} -> {table_name} : {loaded} rows"
    )

conn.close()

print("\nLoad Audit Complete")