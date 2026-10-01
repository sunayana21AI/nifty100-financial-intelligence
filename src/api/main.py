"""
src/api/main.py
FastAPI server with 16 endpoints.
"""
import sqlite3
import time
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"

app = FastAPI(
    title="Nifty 100 Analytics API",
    version="1.0.0",
    description="REST API for Nifty 100 financial intelligence",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    dur = (time.time() - start) * 1000
    print(f"[{request.method}] {request.url.path} → {response.status_code} ({dur:.0f}ms)")
    return response


START_TIME = time.time()


def db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows):
    return [dict(r) for r in rows]


def query(sql, params=()):
    conn = db()
    try:
        cur = conn.execute(sql, params)
        return rows_to_dicts(cur.fetchall())
    finally:
        conn.close()


# ---------- Health ----------
@app.get("/api/v1/health")
def health():
    tables = ["companies", "financial_ratios", "profitandloss",
              "balancesheet", "cashflow", "sectors", "peer_groups",
              "peer_percentiles", "documents", "stock_prices"]
    counts = {}
    conn = db()
    try:
        for t in tables:
            try:
                counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                counts[t] = 0
    finally:
        conn.close()

    return {
        "status": "ok",
        "db_row_counts": counts,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": "1.0.0",
    }


# ---------- Companies ----------
@app.get("/api/v1/companies")
def list_companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
):
    sql = """
        SELECT c.ticker AS company_id, c.company_name,
               s.broad_sector AS sector, s.sub_sector,
               s.market_cap_category,
               r.return_on_equity_pct AS roe_pct,
               r.return_on_capital_employed_pct AS roce_pct
        FROM companies c
        LEFT JOIN sectors s ON s.ticker = c.ticker
        LEFT JOIN financial_ratios r ON r.company_id = c.ticker
            AND r.year = (SELECT MAX(year) FROM financial_ratios
                          WHERE company_id = c.ticker)
        WHERE 1=1
    """
    params = []
    if sector:
        sql += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        sql += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        sql += " AND (c.ticker LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += " ORDER BY c.ticker"
    return query(sql, params)


@app.get("/api/v1/companies/{ticker}")
def get_company(ticker: str):
    rows = query("""
        SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category,
               r.*
        FROM companies c
        LEFT JOIN sectors s ON s.ticker = c.ticker
        LEFT JOIN financial_ratios r ON r.company_id = c.ticker
            AND r.year = (SELECT MAX(year) FROM financial_ratios
                          WHERE company_id = c.ticker)
        WHERE c.ticker = ?
    """, [ticker])
    if not rows:
        raise HTTPException(404, f"Company {ticker} not found")
    return rows[0]


@app.get("/api/v1/companies/{ticker}/pl")
def get_pl(ticker: str, from_year: str | None = None, to_year: str | None = None):
    sql = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker]
    if from_year:
        sql += " AND year_int >= ?"
        params.append(int(from_year[:4]))
    if to_year:
        sql += " AND year_int <= ?"
        params.append(int(to_year[:4]))
    sql += " ORDER BY year_int"
    return query(sql, params)


@app.get("/api/v1/companies/{ticker}/bs")
def get_bs(ticker: str, from_year: str | None = None, to_year: str | None = None):
    sql = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker]
    if from_year:
        sql += " AND year_int >= ?"
        params.append(int(from_year[:4]))
    if to_year:
        sql += " AND year_int <= ?"
        params.append(int(to_year[:4]))
    sql += " ORDER BY year_int"
    return query(sql, params)


@app.get("/api/v1/companies/{ticker}/cashflow")
def get_cf(ticker: str, from_year: str | None = None, to_year: str | None = None):
    # Cashflow uses int company_id
    comp = query("SELECT company_id FROM companies WHERE ticker = ?", [ticker])
    if not comp:
        raise HTTPException(404, f"Company {ticker} not found")
    num_id = comp[0]["company_id"]

    sql = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [num_id]
    if from_year:
        sql += " AND year_int >= ?"
        params.append(int(from_year[:4]))
    if to_year:
        sql += " AND year_int <= ?"
        params.append(int(to_year[:4]))
    sql += " ORDER BY year_int"
    return query(sql, params)


@app.get("/api/v1/companies/{ticker}/ratios")
def get_ratios(ticker: str, year: int | None = None):
    sql = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year:
        sql += " AND year = ?"
        params.append(year)
    sql += " ORDER BY year"
    return query(sql, params)


@app.get("/api/v1/companies/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    pdf = ROOT / "reports" / "tearsheets" / f"{ticker}_tearsheet.pdf"
    if not pdf.exists():
        raise HTTPException(404, f"Tearsheet not found for {ticker}")
    return FileResponse(str(pdf), media_type="application/pdf",
                        filename=f"{ticker}_tearsheet.pdf")


# ---------- Screener ----------
@app.get("/api/v1/screener")
def screener(
    min_roe: float | None = None,
    max_de: float | None = None,
    min_fcf: float | None = None,
    sector: str | None = None,
    min_rev_cagr_5yr: float | None = None,
    min_pat_cagr_5yr: float | None = None,
    max_pe: float | None = None,
):
    if min_roe is not None and min_roe < -100:
        raise HTTPException(400, "min_roe must be >= -100")
    if max_de is not None and max_de < 0:
        raise HTTPException(400, "max_de must be >= 0")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(400, "max_pe must be >= 0")

    sql = """
        SELECT c.ticker AS company_id, c.company_name,
               s.broad_sector AS sector,
               r.return_on_equity_pct AS roe,
               r.debt_to_equity,
               r.free_cash_flow_cr AS fcf,
               r.revenue_cagr_5yr,
               r.pat_cagr_5yr,
               r.pe_ratio AS pe
        FROM companies c
        LEFT JOIN sectors s ON s.ticker = c.ticker
        JOIN financial_ratios r ON r.company_id = c.ticker
            AND r.year = (SELECT MAX(year) FROM financial_ratios
                          WHERE company_id = c.ticker)
        WHERE 1=1
    """
    params = []
    if min_roe is not None:
        sql += " AND r.return_on_equity_pct >= ?"
        params.append(min_roe)
    if max_de is not None:
        sql += " AND r.debt_to_equity <= ?"
        params.append(max_de)
    if min_fcf is not None:
        sql += " AND r.free_cash_flow_cr >= ?"
        params.append(min_fcf)
    if sector:
        sql += " AND s.broad_sector = ?"
        params.append(sector)
    if min_rev_cagr_5yr is not None:
        sql += " AND r.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)
    if min_pat_cagr_5yr is not None:
        sql += " AND r.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)
    if max_pe is not None:
        sql += " AND r.pe_ratio <= ?"
        params.append(max_pe)

    sql += " ORDER BY r.return_on_equity_pct DESC"
    return query(sql, params)


# ---------- Sectors ----------
@app.get("/api/v1/sectors")
def list_sectors():
    return query("""
        SELECT s.broad_sector AS sector,
               COUNT(DISTINCT s.ticker) AS company_count,
               ROUND(AVG(r.return_on_equity_pct), 2) AS median_roe,
               ROUND(AVG(r.pe_ratio), 2) AS median_pe,
               ROUND(AVG(r.debt_to_equity), 2) AS median_de
        FROM sectors s
        LEFT JOIN financial_ratios r ON r.company_id = s.ticker
            AND r.year = (SELECT MAX(year) FROM financial_ratios
                          WHERE company_id = s.ticker)
        GROUP BY s.broad_sector
        ORDER BY company_count DESC
    """)


@app.get("/api/v1/sectors/{sector}/companies")
def companies_in_sector(sector: str):
    rows = query("""
        SELECT c.ticker AS company_id, c.company_name,
               r.return_on_equity_pct AS roe,
               r.pe_ratio AS pe,
               r.debt_to_equity
        FROM companies c
        JOIN sectors s ON s.ticker = c.ticker
        LEFT JOIN financial_ratios r ON r.company_id = c.ticker
            AND r.year = (SELECT MAX(year) FROM financial_ratios
                          WHERE company_id = c.ticker)
        WHERE s.broad_sector = ?
        ORDER BY c.ticker
    """, [sector])
    if not rows:
        raise HTTPException(404, f"No companies in sector {sector}")
    return rows


# ---------- Peers ----------
@app.get("/api/v1/peers/{group_name}")
def get_peers(group_name: str):
    rows = query("""
        SELECT * FROM peer_percentiles WHERE peer_group_name = ?
    """, [group_name])
    if not rows:
        raise HTTPException(404, f"Peer group {group_name} not found")
    return rows


@app.get("/api/v1/companies/{ticker}/peers/compare")
def peer_compare(ticker: str):
    rows = query("""
        SELECT peer_group_name FROM peer_percentiles
        WHERE company_id = ? LIMIT 1
    """, [ticker])
    if not rows:
        raise HTTPException(404, f"No peer group for {ticker}")
    group = rows[0]["peer_group_name"]

    data = query("""
        SELECT company_id, metric, value, percentile_rank
        FROM peer_percentiles
        WHERE peer_group_name = ?
    """, [group])

    return {"ticker": ticker, "peer_group": group, "metrics": data}


# ---------- Market Cap / Valuation ----------
@app.get("/api/v1/market-cap/{ticker}")
def market_cap(ticker: str):
    return query("""
        SELECT year, pe_ratio AS pe, pb_ratio AS pb,
               dividend_yield_pct
        FROM financial_ratios
        WHERE company_id = ? AND year >= 2019
        ORDER BY year
    """, [ticker])


# ---------- Portfolio Stats ----------
@app.get("/api/v1/portfolio/stats")
def portfolio_stats():
    df_path = ROOT / "output" / "portfolio_stats.csv"
    if not df_path.exists():
        raise HTTPException(404, "Portfolio stats not generated yet")
    import pandas as pd
    return pd.read_csv(df_path).to_dict(orient="records")


# ---------- Documents ----------
@app.get("/api/v1/companies/{ticker}/documents")
def documents(ticker: str):
    return query("""
        SELECT * FROM documents WHERE company_id = ?
    """, [ticker])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)