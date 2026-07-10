import pandas as pd
from pathlib import Path

for file in Path("data/clean").glob("*.xlsx"):

    print("\n")
    print("=" * 80)

    print(file.name)

    df = pd.read_excel(file)

    print(df.shape)

    print(df.columns.tolist())

    print(df.head(2))