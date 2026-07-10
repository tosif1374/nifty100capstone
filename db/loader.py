import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "db/nifty100.db"
DATA_PATH = Path("data/clean")

conn = sqlite3.connect(DB_PATH)

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

for file_name, table_name in FILES.items():

    file_path = DATA_PATH / file_name

    print(f"\nLoading {file_name} -> {table_name}")

    df = pd.read_excel(file_path)

    # normalize column names
    df.columns = [
        str(col)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("%", "pct")
        .replace("/", "_")
        for col in df.columns
    ]

    print(f"Rows: {len(df)}")

    df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False
    )

print("\nAll tables loaded successfully.")

conn.close()