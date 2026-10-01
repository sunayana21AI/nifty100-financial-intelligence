# Sprint 5 Retrospective — Intelligence, NLP & PDF Reports

**Duration:** Days 29–35  
**Story Points:** 70 SP  
**Epics:** 07 (Cash Flow Intelligence), 08 (Reports), 09 (NLP)  
**Status:** ✅ Complete

---

## 🎯 Sprint Goal

Build NLP module for auto-generated pros/cons, Cash Flow Intelligence module, and PDF report suite (92 tearsheets + sector + portfolio).

**Outcome:** ✅ Fully achieved.

---

## ✅ What Went Well

1. **NLP parser** — Extracted 63 CAGR values from messy text with regex
2. **Pros/cons generator** — 12+12 rules + universal fallbacks → 100% coverage
3. **Cashflow intelligence** — 8-capital-allocation pattern classification
4. **Tearsheet PDFs** — 91 companies generated without errors
5. **Sector reports** — All 10 sectors covered
6. **Handled data quirks** — int/str company_id, year_int, orphan tickers, NaN year_int

---

## 🐛 Bugs Found & Fixed

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | Parser returned 0 values | Title row at index 0 pushed headers to row 1 | `skiprows=1` in read_excel |
| 2 | Parse failures for "TTM: 43%" | Regex only matched "X Years: Y%" | Documented — TTM not a CAGR |
| 3 | Pros/cons missing for some companies | Rules too strict | Added P13/C13 fallbacks + universal P99/C99 |
| 4 | Cashflow 100% Unknown | cashflow.company_id is INT, ratios is ticker | Map int→ticker via companies table |
| 5 | Cashflow year string "Mar-13" | Year format inconsistent | Use year_int column |
| 6 | 8 orphan tickers in ratios | Sprint 1 ETL incomplete | Filter `ratios ∩ companies` |
| 7 | 92 rows expected, 100 shown | Orphan tickers | Filter to master list |
| 8 | Charts blank in tearsheet PDF | `Drawing` object not wrapped | Wrap in Table |
| 9 | Cashflow empty in tearsheet | numeric_id fetch wrong | Query by int(company_id) |
| 10 | PDF size too small (4 KB) | Small charts | Bigger charts + `_wrap_chart()` |
| 11 | `cannot convert NaN to integer` | NaN in year_int | `pd.notna(y)` guard + drop NaN rows |
| 12 | ATGL "Unknown" cashflow | No cashflow data in DB (ETL issue) | Documented — Sprint 6 fix |

---

## 📊 Deliverables Produced

| File | Rows / Size | Status |
|------|-------------|--------|
| `output/analysis_parsed.csv` | 63 values | ✅ |
| `output/parse_failures.csv` | 17 | ✅ |
| `output/cagr_divergences.csv` | 2 | ✅ |
| `output/pros_cons_generated.csv` | 565 entries | ✅ |
| `output/cashflow_intelligence.xlsx` | 92 rows, 3 sheets | ✅ |
| `output/distress_alerts.csv` | 13 | ✅ |
| `output/capital_allocation.csv` | 91 rows | ✅ |
| `output/pattern_changes.csv` | 418 | ✅ |
| `reports/tearsheets/*.pdf` | 91 files | ✅ |
| `reports/sector/*.pdf` | 10 files | ✅ |
| `reports/portfolio/portfolio_summary.pdf` | 92 pages | ✅ |
| `output/skipped_tearsheets.csv` | 1 (JIOFIN) | ✅ |

---

## 🔍 Data Edge Cases Discovered

1. **Analysis file** only has **20 companies** (not 92) — parser scope limited
2. **TTM / 1-Year** entries in analysis — not CAGR, correctly skipped
3. **8 orphan tickers** in `financial_ratios` but not in `companies`:
   ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VEDL, WIPRO, ZOMATO, ZYDUSLIFE
4. **ATGL** — valid company but no cashflow data in DB (ETL issue)
5. **JIOFIN** — only 2 years of data (skipped, logged)
6. **`cashflow.company_id`** is INT, while `ratios.company_id` is ticker string
7. **`year` format varies** — "Mar-13" vs "Dec 2012" vs plain 2012 → use `year_int`
8. **Duplicate rows** in cashflow and balancesheet (same year twice)

---

## 🎨 Design Decisions

1. **Universal fallback rules** (P99, C99) — guarantee 100% coverage
2. **8 capital allocation patterns** based on (CFO, CFI, CFF) signs
3. **CFO Quality** = avg(CFO/PAT) over 5 years (High > 1.0, Moderate 0.5-1.0, Accrual Risk < 0.5)
4. **CapEx Intensity** = |investing| / sales × 100 (Asset Light < 3, Moderate 3-8, Capital Intensive > 8)
5. **Distress Signal** = CFO < 0 AND CFF > 0
6. **ReportLab charts wrapped in Table** — needed for rendering
7. **Trend arrows** with ±2% threshold for "flat"

---

## ⚡ Performance

| Task | Time |
|------|------|
| Parser run | ~1 sec |
| Pros/cons generation | ~5 sec |
| Cashflow intelligence | ~3 sec |
| 91 tearsheets batch | ~90 sec |
| 10 sector PDFs | ~10 sec |
| Portfolio summary | ~30 sec |

---

## 📚 Lessons Learned

1. **Regex patterns** need real-data testing — title rows, extra spaces, missing colons
2. **Fallback rules** are essential for 100% coverage requirements
3. **Type mismatches** (int vs str) across tables are common — normalize early
4. **ReportLab Drawing** must be wrapped in Table for correct rendering
5. **NaN handling** in chart labels prevents batch failures
6. **Skipping criteria** (< 3 years data) prevents crashes on partial data
7. **Batch logging** of skipped/failed tickers critical for reproducibility

---

## 🎯 Sprint 6 Action Items

| # | Item | Priority |
|---|------|----------|
| 1 | Fix ATGL cashflow data in ETL | Medium |
| 2 | Add 8 orphan tickers to companies/sectors OR filter at ETL | High |
| 3 | Add analysis.xlsx entries for all 92 companies | Medium |
| 4 | Standardize year format across all tables | High |
| 5 | Move to SQLAlchemy or ORM for cleaner joins | Low |
| 6 | Add unit tests for parser regex patterns | Medium |
| 7 | Add integration test for tearsheet generation | Medium |
| 8 | Consider `weasyprint` for HTML→PDF with bigger output | Low |

---

## ✅ Definition of Done — Verified

- [x] `pros_cons_generated.csv` has ≥ 1 pro and 1 con for every company (565 entries, 100%)
- [x] 91 tearsheets exist in `reports/tearsheets/` (88 + 3 retried)
- [x] Visual review confirmed no overflow, no blank pages
- [x] `cashflow_intelligence.xlsx` has 92 rows with all required columns
- [x] 10 sector PDFs generated (10 sectors in DB, not 11)
- [x] Portfolio summary PDF generated
- [x] Sprint 5 review ready

**Signed off:** ✅ Sprint 5 Complete

---

**Author:** Development Team  
**Date:** October 2026