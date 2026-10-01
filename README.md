# 📊 Nifty 100 Financial Intelligence Platform

End-to-end financial analytics platform for 92 Nifty 100 companies — from raw Excel data and ETL pipelines to financial analytics, intelligent screening, peer comparison, interactive Streamlit dashboard, REST API, ML clustering, and automated PDF reports.

**6 Sprints Complete** ✅ | **112 Tests Passing** ✅ | **19/20 Acceptance Gates** ✅

---

## ✨ Features

| Category | Feature |
|----------|---------|
| **Data Engineering** | Excel → SQLite ETL pipeline for 92 Nifty 100 companies |
| **Financial Analytics** | Financial ratios, CAGR, FCF, profitability, leverage and growth metrics |
| **Screening** | Multi-metric stock screener with 6 investment presets |
| **Scoring** | Composite quality scoring with sector-relative normalization |
| **Peer Analysis** | Peer groups, percentile rankings and peer comparison |
| **Dashboard** | 8-screen Streamlit app (localhost:8501) |
| **API** | 16 REST endpoints via FastAPI (localhost:8000) |
| **Clustering** | KMeans with 5 company archetypes |
| **Analytics** | Financial ratios, CAGR, FCF, peer percentiles |
| **NLP** | Auto-generated pros/cons (12+12 rules) |
| **Valuation** | FCF yield + sector-relative P/E flags |
| **PDF Reports** | 91 tearsheets + 10 sector reports + portfolio summary |
| **Tests** | 112 passing (ETL + KPI + API) |

---

# 🏗️ Project Development — Sprint Overview

The project was developed incrementally across multiple sprints, starting from raw financial datasets and progressing toward a complete financial intelligence platform.

---

## 🟢 Sprint 1 — Data Engineering & ETL

**Goal:** Build the foundation for the Nifty 100 financial intelligence platform by converting raw Excel datasets into a structured SQLite database.

### Key Work

- Collected and organized financial datasets for 92 Nifty 100 companies
- Designed the SQLite relational database schema
- Created core company and financial tables
- Built Excel → SQLite ETL pipelines
- Loaded:
  - Company information
  - Sector classification
  - Profit & Loss data
  - Balance Sheet data
  - Cash Flow data
  - Financial ratios
  - Stock prices
  - Market capitalization
  - Peer groups
  - Annual report/document links
  - Pros and cons
- Added foreign-key relationships between financial tables and companies
- Implemented data validation and quality checks
- Handled missing and inconsistent financial data

### Main Output
<img width="1847" height="993" alt="image" src="https://github.com/user-attachments/assets/a971213c-7a09-45cc-ab2c-4014581525c9" />
<img width="1898" height="1013" alt="image" src="https://github.com/user-attachments/assets/88901162-65d3-4d12-8508-03c37776ace4" />
<img width="1877" height="887" alt="image" src="https://github.com/user-attachments/assets/adb3bd54-6ded-41bd-b480-c748c7cf2122" />
<img width="1270" height="976" alt="image" src="https://github.com/user-attachments/assets/5741a5c3-80db-49dd-87c2-f50ab2b1df9f" />
<img width="987" height="445" alt="image" src="https://github.com/user-attachments/assets/b4aa5e77-6e92-49c6-8743-f4bdc35ecab4" />

```text
db/
└── nifty100.db

data/
└── raw/
    ├── companies.xlsx
    ├── sectors.xlsx
    ├── profitandloss.xlsx
    ├── balancesheet.xlsx
    ├── cashflow.xlsx
    ├── financial_ratios.xlsx
    ├── stock_prices.xlsx
    ├── market_cap.xlsx
    ├── peer_groups.xlsx
    └── ...

Result: A structured financial database containing the historical data required for downstream analytics.

🔵 Sprint 2 — Financial Analytics & KPI Engine

Goal: Transform raw financial data into meaningful company-level financial metrics.

Key Work
Built financial ratio calculation pipelines
Calculated profitability metrics:
ROE
ROA
Net Profit Margin
Operating Profit Margin
Calculated leverage metrics:
Debt-to-Equity
Interest Coverage Ratio
Calculated efficiency metrics:
Asset Turnover
Calculated growth metrics:
Revenue CAGR
PAT CAGR
EPS CAGR
Added cash-flow metrics:
Free Cash Flow
Cash from Operations
Added valuation metrics:
P/E
P/B
Dividend Yield
EV/EBITDA
Added market-cap information
Built reusable ratio-loading and analytics modules
Added handling for:
Missing values
Debt-free companies
Financial-sector exceptions
Incomplete historical data
Example KPI Layer
Raw Financial Data
        ↓
Data Cleaning
        ↓
Ratio Calculations
        ↓
Growth & CAGR
        ↓
Cash Flow Metrics
        ↓
Valuation Metrics
        ↓
financial_ratios

Result: A reusable financial KPI layer that powers the screener, peer analysis, valuation and dashboard.

🟣 Sprint 3 — Intelligent Screener & Peer Analytics

Goal: Build a multi-factor stock screening and company comparison engine.

🔎 Multi-Metric Screener

Implemented filtering based on:

ROE
Debt-to-Equity
Free Cash Flow
Revenue CAGR
PAT CAGR
Operating Profit Margin
P/E
P/B
Dividend Yield
Interest Coverage
Market Cap
Net Profit
EPS CAGR
Asset Turnover
Sales
📋 Screening Presets

Six predefined screening strategies:

Quality Compounder
Value Pick
Growth Accelerator
Dividend Champion
Debt-Free Blue Chip
Turnaround Watch
🧮 Composite Quality Score

Implemented a weighted composite scoring model based on:

Profitability — 35%
Cash Quality — 30%
Growth — 20%
Leverage — 15%

The scoring engine includes winsorization and sector-relative normalization to make comparisons more meaningful across sectors.

👥 Peer Analytics

Implemented:

11 peer groups
Peer-level financial metric comparison
Percentile ranking within peer groups
Peer median benchmarks
Company vs peer analysis
📊 Visualization & Reports

Generated:

Company radar charts
Peer comparison Excel workbook
Composite score reports
Screener output
Peer percentile data
Sprint 3 Results
Companies scored       → 92-company universe
Peer groups             → 11
Radar charts            → 92
Companies with peers    → 56
Companies without peers → 36
DQ tests passed         → 14/14

Result: A complete financial screening and peer-analysis engine ready to power the dashboard.

🚀 Sprint 4 — Dashboard & Valuation

Goal: Build the interactive Streamlit financial intelligence dashboard and valuation module.

Dashboard

Implemented an 8-screen Streamlit application:

01 Home
02 Company Profile
03 Screener
04 Peers
05 Trends
06 Sectors
07 Capital Allocation
08 Reports
Dashboard Capabilities
Company search
Financial KPI cards
Historical financial trends
Interactive Plotly charts
Screener filters
Screening presets
Peer comparison
Radar charts
Sector analysis
Capital allocation analysis
Annual report links
CSV export
Valuation

Implemented:

FCF Yield
Sector median P/E
P/E relative valuation
Discount / Fair / Caution flags
Valuation summary Excel output
Valuation flags CSV
Main Outputs
output/
├── valuation_summary.xlsx
└── valuation_flags.csv
🚀 Sprint 5 — API & Machine Learning

Goal: Expose financial analytics through a REST API and add company clustering.

FastAPI

Implemented 16 REST API endpoints for accessing:

Company information
Financial ratios
Profit & Loss
Balance Sheet
Cash Flow
Stock prices
Peer data
Valuation
Screening results
Analytics

API:

http://localhost:8000

Swagger documentation:

http://localhost:8000/docs
Machine Learning

Implemented KMeans clustering to identify 5 company archetypes based on financial characteristics.

Example pipeline:

Financial KPIs
      ↓
Feature Preparation
      ↓
Normalization
      ↓
KMeans Clustering
      ↓
5 Company Archetypes
🟠 Sprint 6 — NLP, PDF Reports & Final QA

Goal: Add automated financial insights, reporting and final quality validation.

🤖 NLP-Based Insights

Implemented rule-based automatic generation of:

Company pros
Company cons
Financial observations

Using 12+12 analytical rules.

📄 PDF Reporting

Generated:

91 company tearsheets
10 sector reports
Portfolio summary

Reports combine financial KPIs, valuation information, company insights and analytics into shareable PDF reports.

🧪 Final Testing

Final test suite covers:

ETL
Database integrity
Financial KPI calculations
Analytics
API endpoints
Data quality

112 tests passing ✅

🏆 Final Platform Architecture
                    RAW EXCEL DATA
                          │
                          ▼
                  ┌───────────────┐
                  │   ETL Layer   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  SQLite DB    │
                  │ nifty100.db   │
                  └───────┬───────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
       KPI Analytics   Screener    Peer Analysis
             │            │            │
             └────────────┼────────────┘
                          ▼
                  ┌───────────────┐
                  │  Valuation    │
                  └───────┬───────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Streamlit      FastAPI       ML
        Dashboard        API       Clustering
             │            │            │
             └────────────┼────────────┘
                          ▼
                  ┌───────────────┐
                  │ NLP Insights  │
                  │ & PDF Reports │
                  └───────────────┘
🚀 Quick Start
# 1. Clone & setup
git clone https://github.com/sunayana21AI/nifty100-financial-intelligence.git
cd nifty100-financial-intelligence

# 2. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate

# 3. Install dependencies
python -m pip install -r requirements.txt
python -m pip install reportlab fastapi uvicorn pytest-html

# 4. Launch dashboard
streamlit run src/dashboard/app.py
# → http://localhost:8501

# 5. Launch API (separate terminal)
uvicorn src.api.main:app --port 8000
# → http://localhost:8000/docs
📁 Project Structure
nifty100-financial-intelligence/
│
├── data/
│   └── raw/
│       ├── companies.xlsx
│       ├── sectors.xlsx
│       ├── profitandloss.xlsx
│       ├── balancesheet.xlsx
│       ├── cashflow.xlsx
│       ├── financial_ratios.xlsx
│       ├── market_cap.xlsx
│       ├── stock_prices.xlsx
│       └── ...
│
├── db/
│   └── nifty100.db
│
├── src/
│   ├── analytics/
│   │   ├── ratios.py
│   │   ├── screener.py
│   │   ├── peer.py
│   │   ├── valuation.py
│   │   └── ...
│   │
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── pages/
│   │   └── utils/
│   │
│   └── api/
│       └── main.py
│
├── output/
│   ├── screener_output.xlsx
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx
│   └── valuation_flags.csv
│
├── reports/
│   ├── radar_charts/
│   └── pdf/
│
├── tests/
│
├── requirements.txt
└── README.md
🧪 Testing
pytest

Current status:

112 tests passing ✅

Coverage includes:

ETL validation
Database integrity
Financial KPI calculations
Screener
Peer analytics
Valuation
API endpoints
Data quality
📌 Project Highlights
92 Nifty 100 companies
6 development sprints
8-screen interactive dashboard
16 REST API endpoints
5 ML company archetypes
11 peer groups
92 radar charts
91 company tearsheets
10 sector reports
Automated financial insights
112 passing tests
SQLite-based financial data warehouse
Interactive Plotly visualizations
FastAPI + Streamlit architecture
👩‍💻 Author

Sunayana Sai Nath Saman

B.Tech Computer Science (Artificial Intelligence)

 
