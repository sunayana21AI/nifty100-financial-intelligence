"""
pages/sectors.py
Sector Analysis Screen - Bubble chart and sector KPIs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">🏭 Sector Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyze sectors and their performance</div>', unsafe_allow_html=True)
    
    # Get data
    df = db.get_all_valuation()
    sectors = db.get_sectors()
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Merge with sectors properly
    df = df.merge(sectors, left_on='company_id', right_on='ticker', how='left')
    
    # Check if broad_sector exists after merge
    if 'broad_sector' not in df.columns:
        # Try alternative column names
        if 'broad_sector_x' in df.columns:
            df['broad_sector'] = df['broad_sector_x']
        elif 'broad_sector_y' in df.columns:
            df['broad_sector'] = df['broad_sector_y']
        else:
            st.warning("Sector data not available. Please check database.")
            return
    
    # Sector dropdown
    sector_options = df['broad_sector'].dropna().unique().tolist()
    
    if not sector_options:
        st.warning("No sectors found in data")
        return
    
    selected_sector = st.selectbox("Select Sector", sorted(sector_options))
    
    # Filter by sector
    sector_df = df[df['broad_sector'] == selected_sector]
    
    if sector_df.empty:
        st.warning(f"No companies found in {selected_sector}")
        return
    
    st.markdown(f"### {selected_sector} - {len(sector_df)} companies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        avg_roe = sector_df['return_on_equity_pct'].mean()
        st.metric("Avg ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
    
    with col2:
        avg_pe = sector_df['pe_ratio'].mean()
        st.metric("Avg P/E", f"{avg_pe:.1f}x" if pd.notna(avg_pe) else "N/A")
    
    st.markdown("---")
    
    # Bubble Chart
    st.subheader("📊 Company Bubble Chart")
    
    # Prepare data for bubble chart
    bubble_df = sector_df.copy()
    bubble_df = bubble_df.dropna(subset=['return_on_equity_pct', 'market_cap_crore'])
    
    if not bubble_df.empty:
        # Use sub_sector if available
        color_col = 'sub_sector' if 'sub_sector' in bubble_df.columns else 'broad_sector'
        
        fig = px.scatter(
            bubble_df,
            x='market_cap_crore',
            y='return_on_equity_pct',
            size='market_cap_crore',
            color=color_col,
            hover_name='company_name',
            title=f"{selected_sector} - Market Cap vs ROE (Bubble = Market Cap)",
            labels={
                'market_cap_crore': 'Market Cap (Cr)',
                'return_on_equity_pct': 'ROE (%)'
            }
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for bubble chart")
    
    # Sector median KPI bar chart
    st.subheader("📊 Sector Median KPIs")
    
    sector_summary = df.groupby('broad_sector').agg({
        'return_on_equity_pct': 'median',
        'pe_ratio': 'median',
        'debt_to_equity': 'median'
    }).round(2)
    
    sector_summary = sector_summary.dropna()
    
    if not sector_summary.empty:
        sector_summary = sector_summary.sort_values('return_on_equity_pct', ascending=False)
        
        fig = px.bar(
            sector_summary.reset_index(),
            x='broad_sector',
            y='return_on_equity_pct',
            title='Median ROE by Sector',
            color='return_on_equity_pct',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sector summary data available")


if __name__ == "__main__":
    show()