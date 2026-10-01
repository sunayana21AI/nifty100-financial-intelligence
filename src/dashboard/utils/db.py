"""
src/dashboard/utils/db.py
Shared data loader with caching for Streamlit dashboard.
Provides BOTH raw column names (return_on_equity_pct)
AND friendly aliases (roe) so old + new pages both work.
"""
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"


def _conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


# ---------- Column aliases (raw → friendly) ----------
RENAME_MAP = {
    "return_on_equity_pct":             "roe",
    "return_on_capital_employed_pct":   "roce",
    "return_on_assets_pct":             "roa",
    "net_profit_margin_pct":            "npm",
    "operating_profit_margin_pct":      "opm",
    "pe_ratio":                         "pe",
    "pb_ratio":                         "pb",
    "dividend_yield_pct":               "dividend_yield",
    "free_cash_flow_cr":                "fcf",
    "market_cap_crore":                 "market_cap",
    "earnings_per_share":               "eps",
    "interest_coverage":                "icr",
    "composite_quality_score":          "composite_score",
    "broad_sector":                     "sector",
}


def _add_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add BOTH raw and friendly column names.
    Keeps old pages working while new pages use short names.
    """
    for raw, friendly in RENAME_MAP.items():
        if raw in df.columns and friendly not in df.columns:
            df[friendly] = df[raw]
    return df


# ---------- Basic getters ----------

@st.cache_data(ttl=600, show_spinner=False)
def get_companies() -> pd.DataFrame:
    with _conn() as c:
        df = pd.read_sql("SELECT * FROM companies ORDER BY company_name", c)
        try:
            sec = pd.read_sql(
                "SELECT ticker AS company_id, broad_sector AS sector, sub_sector "
                "FROM sectors", c)
            df = df.merge(sec, on="company_id", how="left")
        except Exception:
            pass
    return _add_aliases(df)


@st.cache_data(ttl=600, show_spinner=False)
def get_ratios(ticker: str, year: int | None = None) -> pd.DataFrame:
    q = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year is not None:
        q += " AND year = ?"
        params.append(year)
    q += " ORDER BY year"
    with _conn() as c:
        df = pd.read_sql(q, c, params=params)
    return _add_aliases(df)   # ← now has BOTH raw + friendly cols


@st.cache_data(ttl=600, show_spinner=False)
def get_ratios_for_year(year: int) -> pd.DataFrame:
    with _conn() as c:
        df = pd.read_sql("""
            SELECT r.*,
                   c.company_name,
                   s.broad_sector AS sector,
                   s.sub_sector
            FROM financial_ratios r
            LEFT JOIN companies c ON c.company_id = r.company_id
            LEFT JOIN sectors s   ON s.ticker = r.company_id
            WHERE r.year = ?
        """, c, params=[year])
    return _add_aliases(df)


@st.cache_data(ttl=600, show_spinner=False)
def get_pl(ticker: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT year, sales, operating_profit, net_profit "
            "FROM profitandloss WHERE company_id = ? ORDER BY year", c,
            params=[ticker])


@st.cache_data(ttl=600, show_spinner=False)
def get_bs(ticker: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT year, total_assets, total_liabilities "
            "FROM balancesheet WHERE company_id = ? ORDER BY year", c,
            params=[ticker])


@st.cache_data(ttl=600, show_spinner=False)
def get_cf(ticker: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT year, operating_cashflow, investing_cashflow, "
            "financing_cashflow FROM cashflow WHERE company_id = ? ORDER BY year",
            c, params=[ticker])


@st.cache_data(ttl=600, show_spinner=False)
def get_sectors() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql("SELECT * FROM sectors", c)


@st.cache_data(ttl=600, show_spinner=False)
def get_peers(group_name: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT * FROM peer_percentiles WHERE peer_group_name = ?",
            c, params=[group_name])


@st.cache_data(ttl=600, show_spinner=False)
def get_peer_groups() -> list[str]:
    with _conn() as c:
        df = pd.read_sql(
            "SELECT DISTINCT peer_group_name FROM peer_percentiles "
            "ORDER BY peer_group_name", c)
    return df["peer_group_name"].dropna().tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_documents(ticker: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT * FROM documents WHERE company_id = ?", c,
            params=[ticker])


@st.cache_data(ttl=600, show_spinner=False)
def get_prosandcons(ticker: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT * FROM prosandcons WHERE company_id = ?", c,
            params=[ticker])


@st.cache_data(ttl=600, show_spinner=False)
def get_stock_prices(ticker: str) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql(
            "SELECT * FROM stock_prices WHERE company_id = ? ORDER BY date",
            c, params=[ticker])


@st.cache_data(ttl=600, show_spinner=False)
def get_all_tickers() -> list[str]:
    """Return TICKERS (not numeric company_id) — matches financial_ratios."""
    df = get_companies()
    if df.empty:
        return []
    # financial_ratios.company_id stores tickers like 'ABB', 'TCS'
    if "ticker" in df.columns:
        return sorted(df["ticker"].dropna().unique().tolist())
    return sorted(df["company_id"].dropna().unique().tolist())


@st.cache_data(ttl=600, show_spinner=False)
def get_years() -> list[int]:
    with _conn() as c:
        df = pd.read_sql(
            "SELECT DISTINCT year FROM financial_ratios ORDER BY year", c)
    return [int(y) for y in df["year"].dropna().tolist()]


@st.cache_data(ttl=600, show_spinner=False)
def get_valuation_summary() -> pd.DataFrame:
    p = OUTPUT_DIR / "valuation_summary.xlsx"
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(p, sheet_name="Summary")
    except Exception:
        return pd.read_excel(p, sheet_name=0)


@st.cache_data(ttl=600, show_spinner=False)
def get_valuation_flags() -> pd.DataFrame:
    p = OUTPUT_DIR / "valuation_flags.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def get_valuation(ticker: str) -> pd.DataFrame:
    df = get_valuation_summary()
    return df[df["company_id"] == ticker] if not df.empty else df


@st.cache_data(ttl=600, show_spinner=False)
def get_all_ratios_latest() -> pd.DataFrame:
    """Latest-year ratios for all companies with aliases."""
    with _conn() as c:
        df = pd.read_sql("""
            SELECT r.*,
                   c.company_name,
                   s.broad_sector AS sector,
                   s.sub_sector
            FROM financial_ratios r
            LEFT JOIN companies c ON c.company_id = r.company_id
            LEFT JOIN sectors s   ON s.ticker = r.company_id
            WHERE r.year = (SELECT MAX(year) FROM financial_ratios)
        """, c)
    return _add_aliases(df)