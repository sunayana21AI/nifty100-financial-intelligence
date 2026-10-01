# Nifty 100 Analytics â€” Analyst Guide

**Version:** 1.0.0 | **Last Updated:** October 2026

## 1. Introduction

Nifty 100 Analytics is an end-to-end financial intelligence platform covering 92 Nifty 100 companies with 14 years of data (2011-2024).

**Components:**
- Streamlit Dashboard (port 8501) â€” 8-screen interactive UI
- FastAPI Server (port 8000) â€” 16 REST endpoints
- SQLite Database â€” 92 companies, 13 tables
- 91 PDF tearsheets + 10 sector reports + portfolio summary
- 112 automated tests (ETL + KPI + API)

## 2. Getting Started

Prerequisites: Python 3.11+, 2 GB disk, modern browser.

Setup:
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install reportlab fastapi uvicorn pytest-html

text

Launch:
streamlit run src/dashboard/app.py
uvicorn src.api.main:app --port 8000

text

## 3. Streamlit Dashboard

8 screens accessible via left sidebar:

1. Home â€” Market overview, KPIs, sector donut
2. Company Profile â€” Individual deep-dive
3. Screener â€” Filter by metrics, export CSV
4. Peer Comparison â€” Radar chart vs peer group
5. Trend Analysis â€” Multi-year trend charts
6. Sector Analysis â€” Bubble + median KPIs
7. Capital Allocation â€” CFO/CFI/CFF patterns
8. Reports â€” Annual report PDF links

Keyboard shortcuts: C = clear cache, R = rerun.

## 4. Screener Guide

Filters:
- Min ROE (%), Max P/E, Max D/E, Min FCF (Cr)

6 Presets:
- Quality: ROE>18, P/E<40, D/E<1
- Value: ROE>10, P/E<20, D/E<2
- Growth: ROE>15, P/E<60, D/E<3
- Dividend: ROE>12, P/E<35, D/E<1.5
- Low Debt: D/E<0.3
- Custom

Export: Click Download CSV â€” columns: company_id, company_name, sector, roe, pe, debt_to_equity, fcf, composite_score.

## 5. Company Profiles

6 KPI Tiles: ROE, ROCE, NPM, D/E, Rev CAGR, FCF.

Charts:
- Revenue and Net Profit (10-year)
- ROE and ROCE dual-axis trend

Sections:
- Company overview (name, sector, sub-sector)
- Pros (green bullets, NLP-generated)
- Cons (red bullets, NLP-generated)

Example TCS 2024: ROE 50.9%, ROCE 50.9%, NPM 19.1%, D/E 0.09, Rev CAGR 10.5%, FCF 50429 Cr.

## 6. Peer Comparison

11 Peer Groups: IT Services, Private Banks, Public Sector Banks, Automobiles, Consumer Finance, FMCG, Pharmaceuticals, Oil and Gas, Power and Utilities, Life Insurance, Steel.

Features:
- Interactive radar chart (8-axis percentile rank)
- Comparison table with all peer companies

## 7. Trend Analysis

12 Metrics: ROE, ROCE, NPM, OPM, P/E, P/B, D/E, FCF, Market Cap, Rev CAGR, PAT CAGR, EPS.

Usage: Select company, choose up to 3 metrics, view interactive 10-year trend.

## 8. Sector Analysis

10 Sectors:
- Communication Services (2 companies)
- Consumer Discretionary (14)
- Consumer Staples (7)
- Energy (14)
- Financials (23)
- Healthcare (6)
- Industrials (10)
- Information Technology (5)
- Materials (9)
- Real Estate (2)

Bubble Chart: X=Market Cap, Y=ROE, size=Market Cap, color=Sector.

## 9. Capital Allocation

8 Patterns based on CFO/CFI/CFF signs:

| Pattern | CFO | CFI | CFF |
|---------|-----|-----|-----|
| Reinvestor | + | - | - |
| Growth Funded by Debt | + | - | + |
| Divestment and Deleverage | + | + | - |
| Cash Accumulator | + | + | + |
| Distress Signal | - | - | + |
| Turnaround | - | + | - |
| Severe Distress | - | - | - |
| Liquidation Mode | - | + | + |

2024 Distribution: Reinvestor 55, Growth Funded by Debt 13, Distress Signal 12, Divestment 7, Turnaround 2, Severe/Liquidation 2.

## 10. Reports and Tearsheets

91 Company Tearsheets: reports/tearsheets/TICKER_tearsheet.pdf
- Page 1: Navy header, 6 KPIs, Revenue/PAT chart, ROE/ROCE chart
- Page 2: Balance Sheet chart, Cash Flow table, Pros/Cons, Capital Allocation badge

10 Sector Reports: reports/sector/Sector_report.pdf
- Sector summary, median KPIs, company table

Portfolio Summary: reports/portfolio/portfolio_summary.pdf
- 92 pages, one per company, trend arrows

## 11. REST API

Base URL: http://localhost:8000/api/v1

16 Endpoints:
- /health, /companies, /companies/ticker
- /companies/ticker/pl, /bs, /cashflow, /ratios, /tearsheet
- /screener, /sectors, /sectors/sector/companies
- /peers/group, /companies/ticker/peers/compare
- /market-cap/ticker, /portfolio/stats
- /companies/ticker/documents

Examples:
curl http://localhost:8000/api/v1/health
curl "http://localhost:8000/api/v1/screener?min_roe=15&max_pe=30"
curl "http://localhost:8000/api/v1/companies/TCS/ratios?year=2024"

text

Python:
import requests
r = requests.get("http://localhost:8000/api/v1/screener?min_roe=15")
companies = r.json()

text

Swagger UI: http://localhost:8000/docs

## 12. Troubleshooting

| Issue | Fix |
|-------|-----|
| Database not found | Verify nifty100.db in root not db/ |
| Year selector no-op | Press C in browser |
| Numeric tickers 1,2,3 | Clear cache and restart |
| Empty PDF charts | Regenerate tearsheets |
| API 404 on root | Use /docs instead |
| 422 error | Check param types |
| Slow dashboard | Press C, check indexes |
| SQLAlchemy DLL error | Not used, uninstall it |

## 13. Glossary

| Term | Meaning |
|------|---------|
| ROE | Return on Equity = Net Profit / Equity x 100 |
| ROCE | Return on Capital Employed |
| NPM | Net Profit Margin |
| OPM | Operating Profit Margin |
| D/E | Debt-to-Equity |
| ICR | Interest Coverage Ratio |
| FCF | Free Cash Flow = CFO - CapEx |
| CFO/CFI/CFF | Cash from Operations/Investing/Financing |
| CAGR | Compound Annual Growth Rate |
| P/E, P/B | Price-to-Earnings, Price-to-Book |
| EPS | Earnings Per Share |
| EBIT | Earnings Before Interest and Taxes |

## 14. Data Sources

Nifty 100 Universe: 92 companies, 14 years (2011-2024), 1,164 ratio rows.

| File | Records |
|------|---------|
| companies.xlsx | 92 |
| financial_ratios.xlsx | 1,164 |
| profitandloss.xlsx | 1,276 |
| balancesheet.xlsx | 1,312 |
| cashflow.xlsx | 1,187 |
| sectors.xlsx | 92 |
| peer_groups.xlsx | 56 |
| peer_percentiles.xlsx | 538 |
| documents.xlsx | 1,585 |
| stock_prices.xlsx | 5,520 |

Data Quality: 14 DQ rules (nulls, duplicates, ranges).
Documents: BSE filings, 1,585 total.

## Appendix A: Ports

| Port | Service |
|------|---------|
| 8501 | Streamlit Dashboard |
| 8000 | FastAPI |

## Appendix B: Keyboard Shortcuts

| Key | Action |
|-----|--------|
| C | Clear cache |
| R | Rerun |
| ? | Show shortcuts |
| Ctrl+C | Stop server |

---

**End of Analyst Guide**

Repository: github.com/sunayana21AI/nifty100-financial-intelligence
