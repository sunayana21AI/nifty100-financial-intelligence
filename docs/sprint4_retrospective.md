# Sprint 4 QA Log — Dashboard & Valuation

**Date:** Day 27, Sprint 4  
**Tester:** Development Team  
**Scope:** 8 screens × 9 tickers (5 sectors + 4 outliers)

---

## 🎯 Test Tickers

| Sector | Ticker | Notes |
|--------|--------|-------|
| IT | TCS | Full history |
| Financials | HDFCBANK | Large cap bank |
| FMCG | HINDUNILVR | Stable |
| Energy | RELIANCE | Conglomerate |
| Healthcare | APOLLOHOSP | Growth |
| **Outliers** | ABB | Verified latest year 2024 |
| **Outliers** | BEL | ROE 4744% (extreme) |
| **Outliers** | HAL | ROE 3816% (extreme) |
| **Outliers** | INDIGO | ROE 892% (extreme) |

---

## ✅ Screen-by-Screen Results

### 🏠 Home — PASS
- ✅ Year selector (2019–2024) updates KPIs correctly
- ✅ Median ROE: 13% (2021), 16% (2024)
- ✅ 6 KPI tiles render
- ✅ Sector donut (11 sectors)
- ✅ Top 5 composite score table
- ⏱️ Load: 1.8s / 0.15s cached

### 🏢 Company Profile — PASS
- ✅ Search dropdown with ticker labels
- ✅ Latest year caption ("📅 Latest year: 2024")
- ✅ 6 KPI tiles: ABB → ROE 32.5%, ROCE 32.5%, NPM 20.5%, D/E 0.02, Rev CAGR 9.7%, FCF ₹797 Cr
- ✅ Revenue & Net Profit chart (10-yr bars + line)
- ✅ ROE & ROCE trend chart
- ✅ Pros/Cons section
- ⏱️ Load: 2.4s / 0.20s cached

### 🔎 Screener — PASS
- ✅ 4 sliders (ROE, P/E, D/E, FCF)
- ✅ 6 presets (Custom, Quality, Value, Growth, Dividend, Low Debt)
- ✅ Live result count (28 default matches)
- ✅ CSV download works — valid file with correct headers
- ✅ Extreme sliders (all max = 92; all min = 0)
- ⏱️ Load: 2.1s / 0.18s cached

### 👥 Peer Comparison — PASS
- ✅ 11 peer groups in dropdown
- ✅ Interactive radar chart (Plotly Scatterpolar)
- ✅ Peer comparison table
- ✅ Empty group handling
- ⏱️ Load: 1.5s / 0.12s cached

### 📈 Trend Analysis — PASS
- ✅ 92 tickers in dropdown (correctly shows tickers, not IDs)
- ✅ Multi-metric selector (up to 3)
- ✅ Line chart with markers
- ✅ Partial data handled (fewer years)
- ⏱️ Load: 0.9s / 0.10s cached

### 🗂️ Sector Analysis — PASS
- ✅ Bubble chart (X=Market Cap, Y=ROE, size, color=sector)
- ✅ Median ROE by sector bar chart
- ✅ All 11 sectors present
- ⏱️ Load: 2.0s / 0.15s cached

### 💰 Capital Allocation — PASS
- ✅ CSV empty → falls back to D/E classification
- ✅ Treemap with 4 patterns
- ✅ Counts: Debt-Free 39, High Debt 26, Moderate 18, Low 16
- ✅ Company list by pattern (filterable)
- ⏱️ Load: 1.2s / 0.10s cached

### 📄 Reports — PASS
- ✅ Ticker dropdown (92 companies)
- ✅ Documents from DB
- ✅ PDF links clickable
- ⏱️ Load: 0.8s / 0.08s cached

---

## 💹 Valuation Module QA

### `valuation.py` Run