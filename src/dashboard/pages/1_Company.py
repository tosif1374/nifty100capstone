# src/dashboard/pages/1_Company.py

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import latest_available_ratio
from api_client import (
    get_companies,
    get_ratios,
    get_pnl,
    get_balance,
    get_cashflow,
    get_peers,
)

from components.charts import (
    ratio_trend_chart,
    margin_trend_chart,
    cashflow_quality_chart,
    balance_bar_chart,
)

st.set_page_config(
    page_title="Company Deep-Dive",
    layout="wide"
)

st.title("🔍 Company Deep-Dive")

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def safe_metric(value, suffix=""):
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


# ---------------------------------------------------------------------
# Company Selector
# ---------------------------------------------------------------------

companies = get_companies()

company_map = {
    c["company_name"]: c["id"]
    for c in companies
}

selected_name = st.selectbox(
    "Select Company",
    sorted(company_map.keys())
)

company_id = company_map[selected_name]

# ---------------------------------------------------------------------
# Ratio Section
# ---------------------------------------------------------------------

ratios_data = get_ratios(company_id)
ratios = ratios_data.get("ratios", [])

if ratios:

    roe = latest_available_ratio(
        ratios,
        "roe_pct"
    )

    roce = latest_available_ratio(
        ratios,
        "roce_pct"
    )

    de_ratio = latest_available_ratio(
        ratios,
        "de_ratio"
    )

    icr = latest_available_ratio(
        ratios,
        "icr"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "ROE %",
        safe_metric(roe, "%"),
        help="Return on Equity"
    )

    c2.metric(
        "ROCE %",
        safe_metric(roce, "%"),
        help="Return on Capital Employed"
    )

    c3.metric(
        "D/E Ratio",
        safe_metric(de_ratio),
        help="Debt to Equity Ratio"
    )

    c4.metric(
        "ICR",
        safe_metric(icr, "x"),
        help="Interest Coverage Ratio"
    )

    st.plotly_chart(
        ratio_trend_chart(
            ratios,
            f"{selected_name} — Ratio Trends"
        ),
        use_container_width=True
    )

# ---------------------------------------------------------------------
# Profit & Loss Trends
# ---------------------------------------------------------------------

st.subheader("Profit & Loss Trends")

pnl = get_pnl(company_id)

col1, col2 = st.columns(2)

if pnl.get("sales_cagr"):

    sc = pnl["sales_cagr"]

    col1.metric(
        "Sales CAGR (5yr)",
        f"{sc['cagr']*100:.1f}%"
        if sc.get("cagr") is not None
        else "N/A",
        help=f"FY{sc['start_year']} → FY{sc['end_year']}"
    )

if pnl.get("profit_cagr"):

    pc = pnl["profit_cagr"]

    col2.metric(
        "Profit CAGR (5yr)",
        f"{pc['cagr']*100:.1f}%"
        if pc.get("cagr") is not None
        else "N/A"
    )

if pnl.get("margin_series"):

    st.plotly_chart(
        margin_trend_chart(
            pnl["margin_series"]
        ),
        use_container_width=True
    )

if pnl.get("eps_unit_flags", 0) > 0:

    st.warning(
        f"⚠ {pnl['eps_unit_flags']} year(s) flagged for EPS unit inconsistency."
    )

# ---------------------------------------------------------------------
# Balance Sheet Health
# ---------------------------------------------------------------------

st.subheader("Balance Sheet Health")

balance = get_balance(company_id)

if "error" not in balance:

    trend = balance.get(
        "de_trend_3yr"
    )

    if trend is not None:

        delta_label = (
            f"3yr Δ: {'▲' if trend > 0 else '▼'} "
            f"{abs(trend):.2f}"
        )

        st.caption(
            f"D/E Trend: {delta_label} "
            f"({'rising leverage ⚠' if trend > 0.2 else 'stable'})"
        )

    st.plotly_chart(
        balance_bar_chart(balance),
        use_container_width=True
    )

# ---------------------------------------------------------------------
# Cash Flow Quality
# ---------------------------------------------------------------------

st.subheader("Cash Flow Quality")

cf = get_cashflow(company_id)

if "error" not in cf:

    col1, col2 = st.columns([1, 2])

    with col1:

        st.plotly_chart(
            cashflow_quality_chart(cf),
            use_container_width=True
        )

    with col2:

        flag = cf.get(
            "cfo_quality_flag",
            "N/A"
        )

        colours = {
            "excellent": "🟢",
            "acceptable": "🔵",
            "warning": "🟠",
            "red_flag": "🔴"
        }

        st.markdown(
            f"**Quality Flag:** "
            f"{colours.get(flag, '')} "
            f"{flag.upper()}"
        )

        latest_fcf = cf.get(
            "latest_fcf"
        )

        avg_fcf = cf.get(
            "fcf_3yr_avg"
        )

        st.metric(
            "Latest FCF (₹ Cr)",
            "N/A"
            if latest_fcf is None
            else f"{latest_fcf:,.0f}"
        )

        st.metric(
            "3-Year Avg FCF (₹ Cr)",
            "N/A"
            if avg_fcf is None
            else f"{avg_fcf:,.0f}"
        )

# ---------------------------------------------------------------------
# Peer Ranking
# ---------------------------------------------------------------------

st.subheader("Peer Ranking (Sector)")

peers = get_peers(company_id)

if "error" not in peers:

    st.caption(
        f"Sector: {peers.get('sector', 'N/A')} | "
        f"ROE Rank: {peers.get('roe_rank', 'N/A')} / "
        f"{peers.get('n_peers', 'N/A')} | "
        f"ROE Percentile: {peers.get('roe_percentile', 'N/A')}%"
    )