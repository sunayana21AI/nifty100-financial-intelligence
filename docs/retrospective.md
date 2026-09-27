# Sprint 4 Retrospective

## 📅 Sprint Details

- **Sprint:** Sprint 4 — Dashboard & Valuation Module
- **Days:** Day 22–28
- **Story Points:** 55 SP
- **Team:** HA, VI, SA, MA

---

## 🎯 Sprint Goal

By end of Sprint 4, a fully working 8-screen Streamlit dashboard must be running on localhost:8501. All screens must load without errors for any of the 92 company tickers. The valuation module must produce `valuation_summary.xlsx` with FCF yield, P/E flags, and overvaluation/discount labels. CSV export must work on the screener screen.

---

## ✅ What Was Built

### Days 22-23: Dashboard Scaffold & Home/Profile Screens
- ✅ `src/dashboard/app.py` — Main Streamlit entry point
- ✅ `src/dashboard/utils/db.py` — Cached data loader with `@st.cache_data`
- ✅ **Home Screen** — 6 KPI tiles, sector donut chart, top 5 companies by composite score
- ✅ **Company Profile Screen** — Search with autocomplete, 6 KPI tiles, 10-year Revenue & Net Profit chart, ROE & ROCE dual-axis chart, pros and cons display

### Day 24: Screener & Peer Comparison Screens
- ✅ **Screener Screen** — 10 metric sliders, 6 preset buttons, live results table, CSV download
- ✅ **Peer Comparison Screen** — 11 peer group dropdown, radar chart (Plotly Scatterpolar), side-by-side KPI table with benchmark highlight

### Day 25: Remaining 4 Screens
- ✅ **Trend Analysis** — Company search, multi-metric overlay (up to 3 metrics), YoY % change annotations
- ✅ **Sector Analysis** — Sector dropdown, bubble chart (Revenue vs ROE, size = Market Cap), sector median KPI bar chart
- ✅ **Capital Allocation** — Treemap (sector → capital pattern → company), clickable pattern breakdown
- ✅ **Reports Screen** — Downloadable Excel/CSV list, BSE PDF links placeholder

### Day 26: Valuation Module
- ✅ `src/analytics/valuation.py` — FCF yield calculation
- ✅ Sector median P/E calculation
- ✅ Overvaluation/Discount flags: **Caution** (P/E > sector_median × 1.5), **Discount** (P/E < sector_median × 0.7), **Fair**
- ✅ `output/valuation_summary.xlsx` — 92 rows
- ✅ `output/valuation_flags.csv` — 44 flagged companies (14 Caution, 30 Discount)

### Day 27: Integration QA & Bug Fixes
- ✅ All 8 screens tested with 10 tickers across sectors
- ✅ Edge cases handled: partial data (JIOFIN), extreme slider values, missing data
- ✅ Performance: Average load time **4ms** (< 3 seconds)
- ✅ Chart sizing fixed

### Day 28: Documentation
- ✅ README.md updated with dashboard run instructions
- ✅ requirements.txt created
- ✅ Sprint 4 retrospective

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| **Total Companies** | 92 |
| **Peer Groups** | 11 |
| **Financial Metrics** | 10 |
| **Investment Presets** | 6 |
| **Radar Charts** | 92 PNG files |
| **Data Quality Tests** | 14/14 PASSED |
| **Valuation Summary** | 92 companies |
| **Caution Flags** | 14 |
| **Discount Flags** | 30 |
| **Fair Flags** | 48 |

---

## 🔍 Key Findings

### UX Decisions
- Year selector in sidebar for consistent filtering
- Preset buttons auto-fill sliders for quick screening
- Radar charts use dashed line for peer average for clarity
- Gold highlighting for benchmark companies
- `N/A` displayed for missing data instead of crashing

### Data Edge Cases Discovered
- JIOFIN has only 1 year of data → displayed as "Data available note"
- 2 null values for ROE and D/E → displayed as "N/A"
- P/E range: 8.7 – 79.3
- P/E median: 46.2

### Performance Findings
- Caching reduced load times from seconds to milliseconds
- Average load time: 4ms
- Most queries run in < 10ms with caching

---

## 🧩 Challenges Overcome

| Challenge | Solution |
|-----------|----------|
| ROE loading issue (Day 15) | Fixed by loading from Excel directly |
| Balancesheet data (Day 18) | Fixed by parsing Excel correctly |
| Peer percentile join issues (Day 20) | Fixed by using correct column names |
| Composite score column missing (Day 21) | Added column and calculated score |
| Sector Analysis `broad_sector` error | Fixed column mapping after merge |
| Capital Allocation treemap error | Fixed path column names |

---

## ✅ What Went Well
- All 8 Streamlit screens load without errors
- All 92 companies have data
- 14/14 DQ tests passed
- Dashboard is responsive and fast
- Team collaboration was smooth

---

## 🚀 What Could Be Improved
- Add more unit tests for individual functions
- Implement error logging for production
- Add user authentication for multi-user access
- Add email alerts for screener results

---

## 📝 Next Steps
- Day 29-30: Additional features (email alerts, automated screening)
- Production deployment
- User acceptance testing

---

## 👥 Team Sign-off

| Team Member | Status |
|-------------|--------|
| HA | ✅ |
| VI | ✅ |
| SA | ✅ |
| MA | ✅ |

---

## 📅 Sign-off Date

September 2026

---

**✅ Sprint 4 Complete! 🎉**