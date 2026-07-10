# debug_companies.py

import pandas as pd

df = pd.read_excel("data/clean/companies .xlsx")

print(df.columns.tolist())
print()
print(df.head())