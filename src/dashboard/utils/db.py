"""
src/dashboard/utils/db.py
Shared data loader with caching for Streamlit dashboard
"""

import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "nifty100.db"


@st.cache_data(ttl=600)
def get_companies():
    """Get all companies list"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT company_id, ticker, company_name, sector_id
    FROM companies
    ORDER BY company_name
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """Get financial ratios for a specific ticker"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        company_id,
        year,
        return_on_equity_pct,
        return_on_capital_employed_pct,
        net_profit_margin_pct,
        debt_to_equity,
        free_cash_flow_cr,
        revenue_cagr_5yr,
        pat_cagr_5yr,
        eps_cagr_5yr,
        interest_coverage,
        asset_turnover,
        market_cap_crore,
        pe_ratio,
        pb_ratio,
        dividend_yield_pct,
        dividend_payout_ratio_pct,
        composite_quality_score
    FROM financial_ratios
    WHERE company_id = ?
    """
    params = [ticker]
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year DESC"
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    """Get Profit & Loss data for a specific ticker"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT year, sales, operating_profit, net_profit
    FROM profitandloss
    WHERE company_id = ?
    ORDER BY year DESC
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker):
    """Get Balance Sheet data for a specific ticker"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT year, total_assets, total_liabilities, equity_capital, reserves
    FROM balancesheet
    WHERE company_id = ?
    ORDER BY year DESC
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker):
    """Get Cash Flow data for a specific ticker"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT year, operating_cashflow, investing_cashflow, financing_cashflow
    FROM cashflow
    WHERE company_id = ?
    ORDER BY year DESC
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    """Get all sectors data"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT ticker, broad_sector, sub_sector, market_cap_category
    FROM sectors
    ORDER BY broad_sector
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name):
    """Get peer comparison data for a specific peer group"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        company_id,
        peer_group_name,
        metric,
        value,
        percentile_rank,
        year
    FROM peer_percentiles
    WHERE peer_group_name = ?
    """
    df = pd.read_sql(query, conn, params=(group_name,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_groups():
    """Get all peer group names"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT peer_group_name FROM peer_percentiles ORDER BY peer_group_name"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['peer_group_name'].tolist()


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """Get valuation data for a specific ticker"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        f.company_id,
        f.year,
        f.pe_ratio,
        f.pb_ratio,
        f.market_cap_crore,
        f.free_cash_flow_cr,
        c.company_name,
        s.broad_sector
    FROM financial_ratios f
    JOIN companies c ON f.company_id = c.ticker
    LEFT JOIN sectors s ON f.company_id = s.ticker
    WHERE f.company_id = ?
    AND f.year = (SELECT MAX(year) FROM financial_ratios)
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_all_valuation():
    """Get valuation data for all companies"""
    conn = sqlite3.connect(str(DB_PATH))
    query = """
    SELECT 
        f.company_id,
        f.year,
        f.pe_ratio,
        f.pb_ratio,
        f.market_cap_crore,
        f.free_cash_flow_cr,
        f.return_on_equity_pct,
        f.debt_to_equity,
        f.revenue_cagr_5yr,
        f.pat_cagr_5yr,
        f.composite_quality_score,
        f.return_on_capital_employed_pct,
        f.net_profit_margin_pct,
        f.interest_coverage,
        f.asset_turnover,
        f.eps_cagr_5yr,
        f.dividend_yield_pct,
        c.company_name,
        s.broad_sector,
        s.sub_sector
    FROM financial_ratios f
    JOIN companies c ON f.company_id = c.ticker
    LEFT JOIN sectors s ON f.company_id = s.ticker
    WHERE f.year = (SELECT MAX(year) FROM financial_ratios)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Convert numeric columns safely
    numeric_cols = [
        'pe_ratio', 'pb_ratio', 'market_cap_crore', 'free_cash_flow_cr',
        'return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr',
        'pat_cagr_5yr', 'composite_quality_score', 'return_on_capital_employed_pct',
        'net_profit_margin_pct', 'interest_coverage', 'asset_turnover',
        'eps_cagr_5yr', 'dividend_yield_pct'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


@st.cache_data(ttl=600)
def get_latest_year():
    """Get the latest year available in financial_ratios"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT MAX(year) as latest_year FROM financial_ratios"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['latest_year'].iloc[0]


@st.cache_data(ttl=600)
def get_years():
    """Get all years available in financial_ratios"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT year FROM financial_ratios ORDER BY year"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['year'].tolist()


@st.cache_data(ttl=600)
def get_sector_summary(year=None):
    """Get sector-wise summary for a given year"""
    if year is None:
        year = get_latest_year()
    
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        s.broad_sector,
        COUNT(DISTINCT f.company_id) as company_count,
        AVG(f.return_on_equity_pct) as avg_roe,
        AVG(f.pe_ratio) as avg_pe,
        AVG(f.debt_to_equity) as avg_de
    FROM financial_ratios f
    JOIN companies c ON f.company_id = c.ticker
    LEFT JOIN sectors s ON f.company_id = s.ticker
    WHERE f.year = ?
    GROUP BY s.broad_sector
    ORDER BY company_count DESC
    """
    df = pd.read_sql(query, conn, params=(year,))
    conn.close()
    return df