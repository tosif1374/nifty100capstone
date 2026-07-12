# src/screener/presets.py

import pandas as pd


def run_preset(name):
    if name == "quality_compounder":
        return pd.DataFrame(
            {
                "company_id": []
            }
        )

    return pd.DataFrame(
        {
            "company_id": []
        }
    )