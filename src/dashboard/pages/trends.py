"""
pages/trends.py
Trend Analysis Screen - 10-year line charts with multi-metric overlay
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">📈 Trend Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyze company performance trends over time</div>', unsafe_allow_html=True)
    
    # Get companies
    companies = db.get_companies()
    
    if companies.empty:
        st.warning("No companies available")
        return
    
    # Search
    company_options = {}
    for _, row in companies.iterrows():
        label = f"{row['company_name']} ({row['ticker']})"
        company_options[label] = row['ticker']
    
    search = st.selectbox("Select Company", list(company_options.keys()), index=0)
    ticker = company_options[search]
    
    # Get data
    ratios = db.get_ratios(ticker)
    pl = db.get_pl(ticker)
    
    if ratios.empty:
        st.warning(f"No data available for {ticker}")
        return
    
    # Sort by year
    ratios = ratios.sort_values('year')
    pl = pl.sort_values('year')
    
    # Multi-metric selector
    st.markdown("### Select Metrics to Display")
    
    metric_options = {
        'return_on_equity_pct': 'ROE',
        'return_on_capital_employed_pct': 'ROCE',
        'net_profit_margin_pct': 'NPM',
        'debt_to_equity': 'D/E',
        'revenue_cagr_5yr': 'Revenue CAGR',
        'pat_cagr_5yr': 'PAT CAGR',
        'free_cash_flow_cr': 'FCF',
        'pe_ratio': 'P/E',
        'pb_ratio': 'P/B'
    }
    
    selected_metrics = st.multiselect(
        "Choose up to 3 metrics",
        options=list(metric_options.keys()),
        format_func=lambda x: metric_options[x],
        default=['return_on_equity_pct', 'revenue_cagr_5yr']
    )
    
    if not selected_metrics:
        st.info("Please select at least one metric")
        return
    
    # Limit to 3 metrics
    if len(selected_metrics) > 3:
        st.warning("Please select only up to 3 metrics")
        selected_metrics = selected_metrics[:3]
    
    # Create chart
    fig = go.Figure()
    
    colors = ['#1E3A5F', '#E74C3C', '#2ECC71']
    
    for i, metric in enumerate(selected_metrics):
        color = colors[i % len(colors)]
        label = metric_options.get(metric, metric)
        
        fig.add_trace(go.Scatter(
            x=ratios['year'],
            y=ratios[metric],
            mode='lines+markers',
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=8)
        ))
        
        # Add YoY % change annotations
        for j in range(1, len(ratios)):
            prev_val = ratios[metric].iloc[j-1]
            curr_val = ratios[metric].iloc[j]
            if prev_val != 0 and pd.notna(prev_val) and pd.notna(curr_val):
                pct_change = ((curr_val - prev_val) / abs(prev_val)) * 100
                fig.add_annotation(
                    x=ratios['year'].iloc[j],
                    y=curr_val,
                    text=f"{pct_change:+.1f}%",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    font=dict(size=9, color=color),
                    yshift=10
                )
    
    fig.update_layout(
        height=500,
        title=f"{companies[companies['ticker'] == ticker]['company_name'].iloc[0]} ({ticker}) - Trend Analysis",
        xaxis_title="Year",
        yaxis_title="Value",
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show data table
    st.subheader("📊 Data Table")
    display_cols = ['year'] + selected_metrics
    display_cols = [c for c in display_cols if c in ratios.columns]
    st.dataframe(ratios[display_cols], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    show()