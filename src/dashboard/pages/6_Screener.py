import streamlit as st
import pandas as pd
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
from utils import latest_available_ratio

st.set_page_config(
    page_title="Stock Screener",
    layout="wide"
)

st.title("🔎 Fundamental Stock Screener")

st.markdown(
    """
    Screen Nifty100 companies using key financial ratios.
    """
)

# ---------------------------
# Filters
# ---------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    roe_filter = st.slider(
        "Minimum ROE (%)",
        min_value=0,
        max_value=50,
        value=15
    )

with col2:
    roce_filter = st.slider(
        "Minimum ROCE (%)",
        min_value=0,
        max_value=60,
        value=15
    )

with col3:
    de_filter = st.slider(
        "Maximum D/E",
        min_value=0.0,
        max_value=10.0,
        value=1.0,
        step=0.1
    )

with col4:
    icr_filter = st.slider(
        "Minimum ICR",
        min_value=0.0,
        max_value=50.0,
        value=3.0,
        step=0.5
    )

st.divider()

# ---------------------------
# Load Companies
# ---------------------------

companies = get_companies()

if not companies:
    st.error("Unable to load company list.")
    st.stop()

results = []

progress_bar = st.progress(0)

total = len(companies)

# ---------------------------
# Screening Logic
# ---------------------------

for idx, company in enumerate(companies):

    try:

        company_id = company["id"]
        company_name = company["company_name"]

        data = get_ratios(company_id)

        ratios = data.get("ratios", [])

        if not ratios:
            continue

        roe = latest_available_ratio(
            ratios,
            "roe_pct"
        )

        roce = latest_available_ratio(
            ratios,
            "roce_pct"
        )

        de = latest_available_ratio(
            ratios,
            "de_ratio"
        )

        icr = latest_available_ratio(
            ratios,
            "icr"
        )

        if (
            roe is None
            or roce is None
            or de is None
            or icr is None
        ):
            continue

        if (
            roe >= roe_filter
            and roce >= roce_filter
            and de <= de_filter
            and icr >= icr_filter
        ):

            results.append({
                "Company": company_name,
                "ROE (%)": round(float(roe), 2),
                "ROCE (%)": round(float(roce), 2),
                "Debt/Equity": round(float(de), 2),
                "ICR": round(float(icr), 2)
            })

    except Exception:
        pass

    progress_bar.progress(
        (idx + 1) / total
    )

progress_bar.empty()

# ---------------------------
# Results
# ---------------------------

st.subheader("📋 Screening Results")

if not results:

    st.warning(
        "No companies matched the selected criteria."
    )

    st.stop()

df = pd.DataFrame(results)

df = df.sort_values(
    by=["ROCE (%)", "ROE (%)"],
    ascending=False
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Matches",
    len(df)
)

c2.metric(
    "Avg ROE",
    f"{df['ROE (%)'].mean():.2f}%"
)

c3.metric(
    "Avg ROCE",
    f"{df['ROCE (%)'].mean():.2f}%"
)

c4.metric(
    "Avg ICR",
    f"{df['ICR'].mean():.2f}"
)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ---------------------------
# Download Results
# ---------------------------

csv = df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇ Download Results (CSV)",
    data=csv,
    file_name="screener_results.csv",
    mime="text/csv"
)