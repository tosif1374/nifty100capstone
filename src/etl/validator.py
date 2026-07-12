# src/etl/validator.py

def check_pk_uniqueness(df, col):
    dups = df[df[col].duplicated()]

    return [
        {
            "severity": "CRITICAL",
            "detail": str(v)
        }
        for v in dups[col]
    ]


def check_composite_pk(df):
    dups = df[df.duplicated(["company_id", "year"])]

    return [
        {"severity": "CRITICAL"}
        for _ in range(len(dups))
    ]


def check_fk_integrity(df, valid_ids):
    out = []

    for cid in df["company_id"]:
        if cid not in valid_ids:
            out.append(
                {
                    "severity": "CRITICAL",
                    "detail": cid
                }
            )

    return out


def check_bs_balance(row, tolerance_pct=1.0):
    assets = row["total_assets"]
    liab_eq = row["total_liab_and_equity"]

    diff_pct = abs(assets - liab_eq) / assets * 100

    if diff_pct > tolerance_pct:
        return {"severity": "WARNING"}

    return None


def check_opm_crosscheck(row):
    calc = row["operating_profit"] / row["sales"] * 100

    if abs(calc - row["reported_opm"]) > 1:
        return {"severity": "WARNING"}

    return None


def check_positive_sales(row):
    if row["sales"] <= 0:
        return {"severity": "CRITICAL"}

    return None