import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

from api_client import get_companies, get_ratios
from utils import (
    latest_available_ratio,
    safe_metric,
    clean_numeric
)

st.set_page_config(
    page_title="Portfolio Analytics",
    layout="wide"
)

st.title("💼 Portfolio Analytics")

companies = get_companies()

company_map = {
    c["company_name"]: c["id"]
    for c in companies
}

selected = st.multiselect(
    "Select Portfolio Companies",
    sorted(company_map.keys())
)

if not selected:
    st.info("Select one or more companies.")
    st.stop()

rows = []

for company in selected:

    try:

        cid = company_map[company]

        data = get_ratios(cid)

        ratios = data.get("ratios", [])

        if not ratios:
            continue

        rows.append({
            "Company": company,
            "ROE": latest_available_ratio(
                ratios,
                "roe_pct"
            ),
            "ROCE": latest_available_ratio(
                ratios,
                "roce_pct"
            ),
            "D/E": latest_available_ratio(
                ratios,
                "de_ratio"
            ),
            "ICR": latest_available_ratio(
                ratios,
                "icr"
            )
        })

    except Exception:
        pass

df = pd.DataFrame(rows)

if df.empty:
    st.warning("No portfolio data available.")
    st.stop()

avg_roe = clean_numeric(
    df["ROE"]
).mean()

avg_roce = clean_numeric(
    df["ROCE"]
).mean()

avg_de = clean_numeric(
    df["D/E"]
).mean()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Companies",
    len(df)
)

c2.metric(
    "Avg ROE",
    safe_metric(avg_roe, "%")
)

c3.metric(
    "Avg ROCE",
    safe_metric(avg_roce, "%")
)

c4.metric(
    "Avg D/E",
    safe_metric(avg_de)
)

st.subheader("Portfolio Allocation")

allocation = pd.DataFrame({
    "Company": df["Company"],
    "Weight": [100 / len(df)] * len(df)
})

fig = px.pie(
    allocation,
    names="Company",
    values="Weight"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.subheader("Risk vs Return")

risk_df = df.copy()

for col in [
    "ROE",
    "ROCE",
    "D/E"
]:
    risk_df[col] = clean_numeric(
        risk_df[col]
    )

risk_df = risk_df.dropna(
    subset=["ROE", "ROCE", "D/E"]
)

if not risk_df.empty:

    fig2 = px.scatter(
        risk_df,
        x="D/E",
        y="ROE",
        size="ROCE",
        hover_name="Company",
        title="Risk vs Return"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

else:
    st.info(
        "No valid ROE/ROCE data available."
    )

st.subheader("Portfolio Holdings")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)