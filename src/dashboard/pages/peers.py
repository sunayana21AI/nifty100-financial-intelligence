"""
pages/peers.py
Peer Comparison Screen with radar charts
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">👥 Peer Comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Compare companies within their peer groups</div>', unsafe_allow_html=True)
    
    # Get peer groups
    peer_groups = db.get_peer_groups()
    
    if not peer_groups:
        st.warning("No peer groups available")
        return
    
    # Select peer group
    selected_group = st.selectbox("Select Peer Group", peer_groups)
    
    # Get companies for this peer group
    companies = db.get_companies()
    
    # Get peer data
    peer_df = db.get_peers(selected_group)
    
    if peer_df.empty:
        st.warning(f"No data available for {selected_group}")
        return
    
    # Get all valuation data
    df = db.get_all_valuation()
    
    # Filter companies in this peer group
    peer_companies = peer_df['company_id'].unique().tolist()
    group_companies = df[df['company_id'].isin(peer_companies)]
    
    if group_companies.empty:
        st.warning(f"No companies found in {selected_group}")
        return
    
    # Select company for comparison
    company_options = {row['company_name']: row['company_id'] for _, row in group_companies.iterrows()}
    selected_company_name = st.selectbox("Select Company", list(company_options.keys()))
    selected_company = company_options[selected_company_name]
    
    st.markdown("---")
    
    # Radar Chart
    st.subheader("📊 Radar Comparison")
    
    # Prepare data for radar chart
    metrics = [
        'return_on_equity_pct',
        'return_on_capital_employed_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'free_cash_flow_cr',
        'pat_cagr_5yr',
        'revenue_cagr_5yr'
    ]
    
    metric_labels = ['ROE', 'ROCE', 'NPM', 'D/E', 'FCF', 'PAT CAGR', 'Revenue CAGR']
    
    # Get selected company data
    company_data = group_companies[group_companies['company_id'] == selected_company].iloc[0]
    
    # Get peer group averages
    peer_avg = group_companies[metrics].mean()
    
    # Prepare values
    company_values = []
    peer_values = []
    
    for metric in metrics:
        val = company_data.get(metric, 0)
        if pd.isna(val):
            val = 0
        company_values.append(float(val))
        
        peer_val = peer_avg.get(metric, 0)
        if pd.isna(peer_val):
            peer_val = 0
        peer_values.append(float(peer_val))
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=company_values,
        theta=metric_labels,
        fill='toself',
        name=selected_company,
        line=dict(color='red', width=2)
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=peer_values,
        theta=metric_labels,
        fill='toself',
        name=f'{selected_group} Avg',
        line=dict(color='blue', width=2, dash='dash')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(company_values), max(peer_values)) * 1.2 if max(company_values) > 0 else 100]
            )
        ),
        height=500,
        showlegend=True,
        title=f"{selected_company_name} vs {selected_group} Average"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Side-by-side comparison table
    st.subheader("📋 Peer Group Comparison Table")
    
    display_cols = ['company_id', 'company_name', 'broad_sector', 'return_on_equity_pct', 
                   'debt_to_equity', 'pe_ratio', 'revenue_cagr_5yr']
    display_cols = [c for c in display_cols if c in group_companies.columns]
    
    # Highlight selected company
    def highlight_row(row):
        if row['company_id'] == selected_company:
            return ['background-color: #FFD700'] * len(row)
        return [''] * len(row)
    
    styled_df = group_companies[display_cols].style.apply(highlight_row, axis=1)
    st.dataframe(styled_df, use_container_width=True)


if __name__ == "__main__":
    show()