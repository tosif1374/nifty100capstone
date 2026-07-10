import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
CLEAN = Path("data/clean")

CLEAN.mkdir(exist_ok=True)

files_with_metadata = [
    "companies .xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx"
]

for file in files_with_metadata:

    path = RAW / file

    df = pd.read_excel(path, header=None)

    headers = df.iloc[1]

    df = df.iloc[2:].copy()

    df.columns = headers

    df.reset_index(drop=True, inplace=True)

    df.to_excel(
        CLEAN / file,
        index=False
    )

    print(f"Cleaned {file}")

already_clean = [
    "financial_ratios.xlsx",
    "market_cap.xlsx",
    "peer_groups.xlsx",
    "sectors.xlsx",
    "stock_prices.xlsx"
]

for file in already_clean:

    df = pd.read_excel(
        RAW / file
    )

    df.to_excel(
        CLEAN / file,
        index=False
    )

    print(f"Copied {file}")