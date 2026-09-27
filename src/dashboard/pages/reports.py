"""
pages/reports.py
Reports Screen - Annual reports and downloads
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">📄 Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Download reports and view annual report links</div>', unsafe_allow_html=True)
    
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
    
    company_name = companies[companies['ticker'] == ticker]['company_name'].iloc[0]
    
    st.markdown(f"### {company_name} ({ticker})")
    
    # Available reports
    st.subheader("📊 Available Reports")
    
    # List all output files
    output_dir = Path("output")
    
    if output_dir.exists():
        files = list(output_dir.glob("*.xlsx")) + list(output_dir.glob("*.csv"))
        
        if files:
            st.markdown("**Downloadable Reports:**")
            for file in sorted(files):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"📄 {file.name}")
                with col2:
                    st.markdown(f"_{file.stat().st_size:,} bytes_")
                with col3:
                    with open(file, 'rb') as f:
                        st.download_button(
                            label="📥",
                            data=f,
                            file_name=file.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file.suffix == '.xlsx' else "text/csv"
                        )
        else:
            st.info("No reports available")
    else:
        st.info("Reports directory not found")
    
    # Annual report links (placeholder)
    st.subheader("📄 Annual Report Links")
    
    st.info("Annual report links will be available once integrated with BSE API")
    
    # Sample years
    years = [2024, 2023, 2022, 2021, 2020]
    
    for year in years:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{year}**")
        with col2:
            st.markdown("🔗 [BSE Link](https://www.bseindia.com/)")
            # In production: actual BSE PDF links


if __name__ == "__main__":
    show()