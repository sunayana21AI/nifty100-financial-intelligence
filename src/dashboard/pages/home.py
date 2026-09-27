"""
pages/home.py
Home Screen - Summary KPIs, Sector Donut Chart, Top 5 Companies
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">🏠 Nifty 100 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive analytics for Nifty 100 companies</div>', unsafe_allow_html=True)
    
    # Year selector
    try:
        years = db.get_years()
        selected_year = st.selectbox("Select Year", years, index=len(years)-1)
    except:
        st.warning("⚠️ Could not load years. Using default.")
        selected_year = 2024
    
    st.subheader("📊 Key Metrics")
    
    # Get data
    try:
        df = db.get_all_valuation()
        
        if df.empty:
            st.warning("No data available")
            return
        
        # Calculate KPIs
        avg_roe = df['return_on_equity_pct'].mean()
        median_pe = df['pe_ratio'].median()
        median_de = df['debt_to_equity'].median()
        total_companies = len(df)
        median_rev_cagr = df['revenue_cagr_5yr'].median()
        debt_free = len(df[df['debt_to_equity'].fillna(0) == 0])
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("📈 Avg ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
        with col2:
            st.metric("💹 Median P/E", f"{median_pe:.1f}x" if pd.notna(median_pe) else "N/A")
        with col3:
            st.metric("⚖️ Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
        with col4:
            st.metric("🏢 Total Companies", total_companies)
        with col5:
            st.metric("📈 Median Rev CAGR", f"{median_rev_cagr:.1f}%" if pd.notna(median_rev_cagr) else "N/A")
        with col6:
            st.metric("🟢 Debt-Free", debt_free)
        
        st.markdown("---")
        
        # Sector Breakdown
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🏭 Sector Distribution")
            
            sector_counts = df['broad_sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            sector_counts = sector_counts.dropna()
            
            if not sector_counts.empty:
                fig = px.pie(
                    sector_counts,
                    values='Count',
                    names='Sector',
                    title=f'Sector Distribution ({selected_year})',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sector data available")
        
        with col2:
            st.subheader("📊 Top Sectors")
            if not sector_counts.empty:
                st.dataframe(
                    sector_counts.sort_values('Count', ascending=False).head(5),
                    use_container_width=True,
                    hide_index=True
                )
        
        # Top 5 Companies
        st.subheader("🏆 Top 5 Companies by Composite Quality Score")
        
        if 'composite_quality_score' in df.columns:
            top_5 = df.nlargest(5, 'composite_quality_score')
            display_cols = ['company_name', 'company_id', 'broad_sector', 'composite_quality_score', 'return_on_equity_pct']
            display_cols = [c for c in display_cols if c in top_5.columns]
            
            if not top_5.empty:
                st.dataframe(top_5[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No composite score data available")
        else:
            st.info("Composite score data not available")
            
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
    
    st.caption(f"Data as of 2024 | Nifty 100 Analytics v1.0")


if __name__ == "__main__":
    show()