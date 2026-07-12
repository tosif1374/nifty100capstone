# src/etl/normaliser.py

import re

_MONTHS = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}


def normalize_year(raw):
    if raw is None:
        raise ValueError("Year cannot be None")

    s = str(raw).strip()

    # Already normalized YYYY-MM
    if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", s):
        return s

    # Financial year formats: 2022-23
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        return f"20{m.group(2)}-03"

    # Financial year formats: 2022-2023
    m = re.fullmatch(r"(\d{4})-(\d{4})", s)
    if m:
        return f"{m.group(2)}-03"

    # Plain year: 2023
    if re.fullmatch(r"\d{4}", s):
        return f"{s}-03"

    # FY23
    m = re.fullmatch(r"FY(\d{2})", s.upper())
    if m:
        return f"20{m.group(1)}-03"

    # FY2023
    m = re.fullmatch(r"FY(\d{4})", s.upper())
    if m:
        return f"{m.group(1)}-03"

    # Month-Year formats: Mar-23, Mar 23, March-2023
    m = re.fullmatch(r"([A-Za-z]+)[ -](\d{2,4})", s)
    if m:
        mon = m.group(1)[:3].upper()
        yr = m.group(2)

        if mon not in _MONTHS:
            raise ValueError(f"Invalid month: {mon}")

        if len(yr) == 2:
            yr = "20" + yr

        return f"{yr}-{_MONTHS[mon]}"

    raise ValueError(f"Invalid year format: {raw}")


def normalize_ticker(raw):
    if raw is None:
        raise ValueError("Ticker cannot be None")

    ticker = str(raw).strip().upper()

    if not ticker:
        raise ValueError("Ticker cannot be empty")

    # Remove exchange suffixes
    if "." in ticker:
        ticker = ticker.split(".")[0]

    if len(ticker) > 15:
        raise ValueError("Ticker too long")

    return ticker