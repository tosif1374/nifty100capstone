import pandas as pd
import sqlite3
from pathlib import Path

conn = sqlite3.connect("./db/nifty100.db")

df = pd.read_sql_query("""
SELECT
    sector,
    2024 AS year,
    COUNT(*) AS n_companies,
    NULL AS roe_mean,
    NULL AS roe_median,
    NULL AS roce_mean,
    NULL AS de_mean,
    NULL AS op_margin_mean
FROM sector_mapping
GROUP BY sector
ORDER BY sector
""", conn)

Path("data/snapshots").mkdir(parents=True, exist_ok=True)

df.to_csv(
    "data/snapshots/sector_comparison.csv",
    index=False
)

print(df)
print("sector_comparison.csv created")