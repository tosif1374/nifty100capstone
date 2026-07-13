import streamlit as st
import pandas as pd
import json
import os
import sys

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
    page_title="Reports Center",
    layout="wide"
)

st.title("📑 Reports & Export Center")

companies = get_companies()

company_map = {
    c["company_name"]: c["id"]
    for c in companies
}

selected = st.selectbox(
    "Select Company",
    sorted(company_map.keys())
)

cid = company_map[selected]

data = get_ratios(cid)

ratios = data.get(
    "ratios",
    []
)

if not ratios:
    st.warning("No ratio data.")
    st.stop()

latest = ratios[-1].copy()

latest["roe_pct"] = latest_available_ratio(
    ratios,
    "roe_pct"
)

latest["roce_pct"] = latest_available_ratio(
    ratios,
    "roce_pct"
)

latest["icr"] = latest_available_ratio(
    ratios,
    "icr"
)

st.subheader(
    "Latest Ratio Snapshot"
)

st.json(latest)

json_text = json.dumps(
    latest,
    indent=2
)

st.download_button(
    "⬇ Download JSON",
    json_text,
    file_name=f"{selected}_ratios.json"
)

csv = pd.DataFrame(
    [latest]
).to_csv(index=False)

st.download_button(
    "⬇ Download CSV",
    csv,
    file_name=f"{selected}_ratios.csv"
)

st.subheader(
    "Platform Summary"
)

st.metric(
    "Companies Covered",
    len(companies)
)