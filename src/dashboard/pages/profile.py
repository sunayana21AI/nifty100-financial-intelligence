"""
pages/profile.py
Company Profile Screen - Search, KPI tiles, charts, pros & cons
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">🏢 Company Profile</div>', unsafe_allow_html=True)
    
    try:
        # Get companies list
        companies = db.get_companies()
        
        if companies.empty:
            st.warning("No companies found in database")
            return
        
        # Create search options
        company_options = {}
        for _, row in companies.iterrows():
            label = f"{row['company_name']} ({row['ticker']})"
            company_options[label] = row['ticker']
        
        search = st.selectbox(
            "🔍 Search for a company",
            options=list(company_options.keys()),
            index=0
        )
        
        ticker = company_options[search]
        
        if not ticker:
            st.warning("Ticker not found — please try another")
            return
        
        # Get data
        ratios = db.get_ratios(ticker)
        pl = db.get_pl(ticker)
        sectors = db.get_sectors()
        
        if ratios.empty:
            st.warning(f"No financial data found for {ticker}")
            return
        
        # Get sector info
        sector_info = sectors[sectors['ticker'] == ticker]
        broad_sector = sector_info['broad_sector'].iloc[0] if not sector_info.empty else "N/A"
        sub_sector = sector_info['sub_sector'].iloc[0] if not sector_info.empty else "N/A"
        
        # Company name
        company_name = companies[companies['ticker'] == ticker]['company_name'].iloc[0] if not companies.empty else ticker
        
        st.markdown(f"### {company_name} ({ticker})")
        st.caption(f"**Sector:** {broad_sector} | **Sub-Sector:** {sub_sector}")
        
        # Latest year data
        latest = ratios.iloc[0] if not ratios.empty else None
        
        if latest is not None:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                val = latest.get('return_on_equity_pct', None)
                st.metric("ROE", f"{val:.1f}%" if pd.notna(val) else "N/A")
            with col2:
                val = latest.get('return_on_capital_employed_pct', None)
                st.metric("ROCE", f"{val:.1f}%" if pd.notna(val) else "N/A")
            with col3:
                val = latest.get('net_profit_margin_pct', None)
                st.metric("NPM", f"{val:.1f}%" if pd.notna(val) else "N/A")
            with col4:
                val = latest.get('debt_to_equity', None)
                st.metric("D/E", f"{val:.2f}" if pd.notna(val) else "N/A")
            with col5:
                val = latest.get('revenue_cagr_5yr', None)
                st.metric("Rev CAGR (5yr)", f"{val:.1f}%" if pd.notna(val) else "N/A")
            with col6:
                val = latest.get('free_cash_flow_cr', None)
                st.metric("FCF", f"₹{val:.1f} Cr" if pd.notna(val) else "N/A")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Revenue & Net Profit")
            
            if not pl.empty:
                pl_sorted = pl.sort_values('year').tail(10)
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(
                    go.Bar(name="Revenue", x=pl_sorted['year'], y=pl_sorted['sales'], marker_color='#1E3A5F'),
                    secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(name="Net Profit", x=pl_sorted['year'], y=pl_sorted['net_profit'], 
                              mode='lines+markers', line=dict(color='#E74C3C', width=3)),
                    secondary_y=True
                )
                
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_yaxes(title_text="Revenue (Cr)", secondary_y=False)
                fig.update_yaxes(title_text="Net Profit (Cr)", secondary_y=True)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No P&L data available")
        
        with col2:
            st.subheader("📊 ROE & ROCE Trend")
            
            if not ratios.empty:
                ratios_sorted = ratios.sort_values('year').tail(10)
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(
                    go.Bar(name="ROE", x=ratios_sorted['year'], y=ratios_sorted['return_on_equity_pct'], marker_color='#2ECC71'),
                    secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(name="ROCE", x=ratios_sorted['year'], y=ratios_sorted['return_on_capital_employed_pct'],
                              mode='lines+markers', line=dict(color='#E67E22', width=3)),
                    secondary_y=True
                )
                
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_yaxes(title_text="ROE (%)", secondary_y=False)
                fig.update_yaxes(title_text="ROCE (%)", secondary_y=True)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No ratio data available")
                
    except Exception as e:
        st.error(f"⚠️ Error loading company profile: {e}")
        st.info("Please try another ticker or check the database connection.")


if __name__ == "__main__":
    show()