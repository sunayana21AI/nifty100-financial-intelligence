"""
src/analytics/cashflow_kpis.py
Cash Flow Intelligence Module.

Computes for every company:
  - CFO Quality Score  (avg CFO/PAT over 5 years)
  - CapEx Intensity    (|investing| / sales × 100)
  - Distress Signal    (CFO < 0 AND CFF > 0 in latest year)
  - Deleveraging Flag  (CFF < 0 in latest year)
  - Capital Allocation Pattern (8-label classification)

Data quirks handled:
  - cashflow.company_id is INTEGER (87, 88...) → map to ticker
  - profitandloss.company_id is TICKER ('ABB')
  - financial_ratios.company_id is TICKER ('ABB')
  - cashflow.year is "Mar-13" → use year_int
  - profitandloss.year is "Dec 2012" → use year_int
  - 8 orphan tickers exist in ratios but not in companies → filter out

Reads:  nifty100.db
Writes: output/cashflow_intelligence.xlsx (3 sheets)
        output/distress_alerts.csv
        nifty100.db → 'cashflow_intelligence' table
"""
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ==========================================================
# Labels
# ==========================================================
def cfo_quality_label(score):
    if score is None or pd.isna(score):
        return "Unknown"
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def capex_label(pct):
    if pct is None or pd.isna(pct):
        return "Unknown"
    if pct < 3:
        return "Asset Light"
    if pct <= 8:
        return "Moderate"
    return "Capital Intensive"


def capital_allocation_label(cfo, cfi, cff):
    """Classify into one of 8 patterns based on sign of (CFO, CFI, CFF)."""
    if cfo is None or cfi is None or cff is None:
        return "Unknown"
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Unknown"

    signs = (
        "+" if cfo >= 0 else "-",
        "+" if cfi >= 0 else "-",
        "+" if cff >= 0 else "-",
    )
    mapping = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "-"): "Divestment & Deleverage",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "+"): "Distress Signal",
        ("-", "+", "-"): "Turnaround",
        ("-", "-", "-"): "Severe Distress",
        ("-", "+", "+"): "Liquidation Mode",
    }
    return mapping.get(signs, "Other")


# ==========================================================
# Helpers
# ==========================================================
def _num(x):
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


# ==========================================================
# Main
# ==========================================================
def analyze_cashflow():
    print(f"[cashflow] Reading from: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    sectors = pd.read_sql(
        "SELECT ticker, broad_sector, sub_sector FROM sectors", conn)
    companies = pd.read_sql(
        "SELECT ticker, company_id AS numeric_id, company_name FROM companies",
        conn)
    conn.close()

    # ==========================================================
    # NORMALIZE company_id
    # ==========================================================
    # companies.numeric_id → int
    companies["numeric_id"] = pd.to_numeric(
        companies["numeric_id"], errors="coerce")
    id_to_ticker = dict(zip(companies["numeric_id"], companies["ticker"]))

    def resolve_company_id(x):
        """Map int company_id → ticker; pass through strings."""
        try:
            n = pd.to_numeric(x, errors="coerce")
            if pd.notna(n) and n in id_to_ticker:
                return id_to_ticker[n]
            return str(x).strip()
        except Exception:
            return str(x).strip()

    cf["company_id"] = cf["company_id"].apply(resolve_company_id)

    # ==========================================================
    # NORMALIZE year (use year_int where available)
    # ==========================================================
    if "year_int" in cf.columns:
        cf["year"] = pd.to_numeric(cf["year_int"], errors="coerce")
    else:
        cf["year"] = pd.to_numeric(cf["year"], errors="coerce")

    if "year_int" in pl.columns:
        pl["year"] = pd.to_numeric(pl["year_int"], errors="coerce")
    else:
        pl["year"] = pd.to_numeric(pl["year"], errors="coerce")

    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

    # ==========================================================
    # NORMALIZE ticker strings
    # ==========================================================
    for df in (ratios, cf, pl):
        df["company_id"] = df["company_id"].astype(str).str.strip()

    sectors["ticker"] = sectors["ticker"].astype(str).str.strip()
    companies["ticker"] = companies["ticker"].astype(str).str.strip()

    sectors = sectors.rename(columns={"ticker": "company_id"})
    companies = companies.rename(columns={"ticker": "company_id"})

    # ==========================================================
    # FILTER: only companies in master `companies` table
    # (excludes 8 orphan tickers in ratios)
    # ==========================================================
    valid_tickers = set(companies["company_id"].dropna().unique())
    all_ratio_tickers = set(ratios["company_id"].dropna().unique())
    all_tickers = sorted(all_ratio_tickers & valid_tickers)

    print(f"[cashflow] Master companies:     {len(valid_tickers)}")
    print(f"[cashflow] Tickers in ratios:    {len(all_ratio_tickers)}")
    print(f"[cashflow] Orphans filtered out: {len(all_ratio_tickers - valid_tickers)}")
    print(f"[cashflow] Processing:           {len(all_tickers)} companies")

    # ==========================================================
    # PER-COMPANY LOOP
    # ==========================================================
    results = []

    for cid in all_tickers:
        r = ratios[ratios["company_id"] == cid].sort_values("year")
        c = cf[cf["company_id"] == cid].sort_values("year")
        p = pl[pl["company_id"] == cid].sort_values("year")

        sec_row = sectors[sectors["company_id"] == cid]
        comp_row = companies[companies["company_id"] == cid]

        if r.empty:
            continue

        latest_r = r.iloc[-1]

        sector = sec_row.iloc[0]["broad_sector"] if not sec_row.empty else None
        sub_sector = sec_row.iloc[0]["sub_sector"] if not sec_row.empty else None
        company_name = comp_row.iloc[0]["company_name"] if not comp_row.empty else cid

        # ---------- CFO / PAT ratio (5-year avg) ----------
        merged = r.merge(
            p[["company_id", "year", "net_profit"]],
            on=["company_id", "year"], how="left"
        ).merge(
            c[["company_id", "year", "operating_cashflow"]],
            on=["company_id", "year"], how="left"
        )

        def _cfo_pat(row):
            cfo = _num(row.get("operating_cashflow"))
            pat = _num(row.get("net_profit"))
            if cfo is not None and pat is not None and pat > 0:
                return cfo / pat
            return np.nan

        merged["cfo_pat"] = merged.apply(_cfo_pat, axis=1)
        recent = merged["cfo_pat"].dropna().tail(5)
        cfo_quality_score = float(recent.mean()) if not recent.empty else np.nan
        cfo_lbl = cfo_quality_label(cfo_quality_score)

        # ---------- CapEx Intensity (latest year) ----------
        capex_pct = None
        if not c.empty and not p.empty:
            latest_c = c.iloc[-1]
            latest_p = p.iloc[-1]
            sales = _num(latest_p.get("sales"))
            investing = _num(latest_c.get("investing_cashflow"))
            if sales and sales > 0 and investing is not None:
                capex_pct = abs(investing) / sales * 100
        capex_lbl = capex_label(capex_pct)

        # ---------- Latest CFO / CFI / CFF ----------
        cfo_val = cfi_val = cff_val = None
        if not c.empty:
            latest_c = c.iloc[-1]
            cfo_val = _num(latest_c.get("operating_cashflow"))
            cfi_val = _num(latest_c.get("investing_cashflow"))
            cff_val = _num(latest_c.get("financing_cashflow"))

        # ---------- Distress / Deleveraging ----------
        distress = (cfo_val is not None and cff_val is not None and
                    cfo_val < 0 and cff_val > 0)
        deleveraging = (cff_val is not None and cff_val < 0)

        # ---------- FCF CAGR 5yr ----------
        fcf_vals = [_num(x) for x in r["free_cash_flow_cr"].dropna().tolist()]
        fcf_cagr_5yr = None
        if len(fcf_vals) >= 6:
            old, new = fcf_vals[-6], fcf_vals[-1]
            if old and old > 0 and new is not None and new > 0:
                fcf_cagr_5yr = ((new / old) ** (1 / 5) - 1) * 100

        # ---------- FCF Conversion ----------
        latest_pat = _num(p.iloc[-1].get("net_profit")) if not p.empty else None
        latest_fcf = _num(latest_r.get("free_cash_flow_cr"))
        fcf_conv = None
        if latest_pat and latest_pat > 0 and latest_fcf is not None:
            fcf_conv = latest_fcf / latest_pat * 100

        # ---------- Capital Allocation Pattern ----------
        cap_alloc = capital_allocation_label(cfo_val, cfi_val, cff_val)

        results.append({
            "company_id":               cid,
            "company_name":             company_name,
            "sector":                   sector,
            "sub_sector":               sub_sector,
            "cfo_quality_score":        round(cfo_quality_score, 2) if not pd.isna(cfo_quality_score) else None,
            "cfo_quality_label":        cfo_lbl,
            "capex_intensity_pct":      round(capex_pct, 2) if capex_pct is not None else None,
            "capex_label":              capex_lbl,
            "fcf_cagr_5yr":             round(fcf_cagr_5yr, 2) if fcf_cagr_5yr is not None else None,
            "fcf_conversion_pct":       round(fcf_conv, 2) if fcf_conv is not None else None,
            "distress_flag":            bool(distress),
            "deleveraging_flag":        bool(deleveraging),
            "capital_allocation_label": cap_alloc,
            "latest_cfo":               cfo_val,
            "latest_cfi":               cfi_val,
            "latest_cff":               cff_val,
            "latest_net_profit":        latest_pat,
            "latest_year":              int(latest_r["year"]) if pd.notna(latest_r.get("year")) else None,
        })

    df = pd.DataFrame(results)

    # ==========================================================
    # WRITE Excel (3 sheets)
    # ==========================================================
    xlsx_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Intelligence", index=False)
        df[df["distress_flag"] == True].to_excel(
            w, sheet_name="Distress", index=False)
        df[df["deleveraging_flag"] == True].to_excel(
            w, sheet_name="Deleveraging", index=False)

    print(f"✅ Wrote {xlsx_path}")
    print(f"   Rows: {len(df)}")

    # ==========================================================
    # WRITE Distress Alerts CSV
    # ==========================================================
    distress_df = df[df["distress_flag"] == True][[
        "company_id", "company_name", "sector",
        "latest_cfo", "latest_cff", "latest_net_profit", "latest_year"
    ]].copy()
    distress_path = OUTPUT_DIR / "distress_alerts.csv"
    distress_df.to_csv(distress_path, index=False)
    print(f"✅ Wrote {distress_path} ({len(distress_df)} rows)")

    # ==========================================================
    # SUMMARY
    # ==========================================================
    print(f"\n[cashflow] Summary:")
    print(f"   Companies analyzed: {len(df)}")
    print(f"   CFO Quality:  {df['cfo_quality_label'].value_counts().to_dict()}")
    print(f"   CapEx:        {df['capex_label'].value_counts().to_dict()}")
    print(f"   Capital Alloc: {df['capital_allocation_label'].value_counts().to_dict()}")
    print(f"   Distress flags:     {int(df['distress_flag'].sum())}")
    print(f"   Deleveraging flags: {int(df['deleveraging_flag'].sum())}")
    print(f"   Unknown (CFO):  {int((df['cfo_quality_label'] == 'Unknown').sum())}")

    # ==========================================================
    # PERSIST to SQLite
    # ==========================================================
    conn2 = sqlite3.connect(str(DB_PATH))
    df.to_sql("cashflow_intelligence", conn2, if_exists="replace", index=False)
    conn2.close()
    print(f"\n✅ Persisted to DB: 'cashflow_intelligence' table")

    return df


if __name__ == "__main__":
    analyze_cashflow()