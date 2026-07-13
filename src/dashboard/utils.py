import pandas as pd


def latest_available_ratio(ratios, field):
    """
    Returns the most recent non-null value for a ratio.

    Example:
    Mar 2024 -> 32.47
    Sep 2024 -> None
    TTM -> None

    Returns 32.47
    """

    if not ratios:
        return None

    for row in reversed(ratios):

        value = row.get(field)

        if value is None:
            continue

        if value == "":
            continue

        try:
            if pd.isna(value):
                continue
        except Exception:
            pass

        return value

    return None


def safe_metric(value, suffix=""):
    """
    Streamlit metric formatter.

    Example:
    32.47 -> 32.47%
    None -> N/A
    """

    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except Exception:
        pass

    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return str(value)


def clean_numeric(series):
    """
    Convert dataframe column to numeric safely.
    """
    return pd.to_numeric(
        series,
        errors="coerce"
    )