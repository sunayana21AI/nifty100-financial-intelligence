import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from dashboard.utils.db import get_peer_groups, get_peers

st.set_page_config(page_title="Peers", page_icon="👥", layout="wide")
st.title("👥 Peer Comparison")

groups = get_peer_groups()
if not groups:
    st.warning("No peer groups found in DB.")
    st.stop()

group = st.selectbox("Peer Group", groups)
df = get_peers(group)

if df.empty:
    st.info(f"No data for group: {group}")
    st.stop()

st.subheader(f"Peer Group: {group}")
st.dataframe(df, use_container_width=True)

# ---------- Radar if data has the right shape ----------
if {"company_id", "metric", "percentile_rank"}.issubset(df.columns):
    fig = go.Figure()
    for cid, sub in df.groupby("company_id"):
        fig.add_trace(go.Scatterpolar(
            r=sub["percentile_rank"].tolist(),
            theta=sub["metric"].tolist(),
            name=str(cid),
            fill="toself",
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"Radar — {group}",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Radar requires columns: company_id, metric, percentile_rank")
    st.write("Available columns:", df.columns.tolist())