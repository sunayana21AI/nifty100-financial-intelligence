"""
src/analytics/valuation.py
Valuation Module — FCF Yield, P/E flags, overvaluation/discount labels.

Handles the data quirk where:
  - companies.company_id is INTEGER (1, 2, 3)
  - financial_ratios.company_id is TICKER string ('ABB', 'TCS')
  - sectors.ticker is TICKER string
  - financial_ratios has 100 tickers but companies only has 92

Uses companies.ticker as the canonical join key, then filters ratios
to only companies present in the master `companies` table.

Reads:   nifty100.db  (financial_ratios, companies, sectors)
Writes:  output/valuation_summary.xlsx   (sheets: Summary, Caution, Discount)
         output/valuation_flags.csv      (Caution + Discount only)
         nifty100.db → 'valuation' table
"""
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[2]     # src/analytics/ → project root
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------- Core logic ----------
def compute_fcf_yield(fcf_cr: float, market_cap_cr: float) -> float:
    """FCF Yield % = (FCF / Market Cap) × 100."""
    if pd.isna(fcf_cr) or pd.isna(market_cap_cr) or market_cap_cr <= 0:
        return np.nan
    return (fcf_cr / market_cap_cr) * 100.0


def flag_valuation(pe: float, sector_median_pe: float) -> str:
    """Assign Caution / Discount / Fair based on P/E vs sector median."""
    if pd.isna(pe) or pd.isna(sector_median_pe) or sector_median_pe <= 0:
        return "Fair"
    if pe > sector_median_pe * 1.5:
        return "Caution"
    if pe < sector_median_pe * 0.7:
        return "Discount"
    return "Fair"


def run() -> pd.DataFrame:
    """Compute valuation summary and write all outputs."""
    print(f"[valuation] Reading from: {DB_PATH}")

    with sqlite3.connect(str(DB_PATH)) as c:
        companies = pd.read_sql(
            "SELECT company_id, ticker, company_name FROM companies", c)
        ratios = pd.read_sql("SELECT * FROM financial_ratios", c)
        sectors = pd.read_sql(
            "SELECT ticker, broad_sector, sub_sector FROM sectors", c)

    # ---------- Normalize join keys to STRING ----------
    companies["company_key"] = companies["ticker"].astype(str).str.strip()
    ratios["company_key"]    = ratios["company_id"].astype(str).str.strip()
    sectors["company_key"]   = sectors["ticker"].astype(str).str.strip()

    # ---------- Filter ratios to only companies in master list ----------
    valid_tickers = set(companies["company_key"].dropna().unique())
    before = ratios["company_key"].nunique()
    ratios = ratios[ratios["company_key"].isin(valid_tickers)].copy()
    after = ratios["company_key"].nunique()
    print(f"[valuation] Filtered ratios: {before} → {after} unique tickers")

    # ---------- Latest year per company ----------
    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")
    ratios = ratios.dropna(subset=["year"])

    latest = (ratios.sort_values("year")
                    .groupby("company_key", as_index=False)
                    .tail(1))

    # ---------- Merge sector ----------
    latest = latest.merge(
        sectors[["company_key", "broad_sector", "sub_sector"]],
        on="company_key", how="left"
    )

    # ---------- Merge company name ----------
    latest = latest.merge(
        companies[["company_key", "company_name"]],
        on="company_key", how="left"
    )

    # ---------- FCF Yield ----------
    latest["fcf_yield_pct"] = latest.apply(
        lambda r: compute_fcf_yield(
            r.get("free_cash_flow_cr"),
            r.get("market_cap_crore"),
        ), axis=1
    )

    # ---------- Sector median P/E ----------
    latest["pe_ratio"] = pd.to_numeric(latest["pe_ratio"], errors="coerce")
    sector_median = (latest.groupby("broad_sector")["pe_ratio"]
                            .median()
                            .rename("sector_median_pe"))
    latest = latest.merge(sector_median, on="broad_sector", how="left")

    # ---------- P/E vs sector median % ----------
    latest["pe_vs_sector_median_pct"] = (
        (latest["pe_ratio"] - latest["sector_median_pe"])
        / latest["sector_median_pe"] * 100.0
    )

    # ---------- Flag ----------
    latest["pe_flag"] = latest.apply(
        lambda r: flag_valuation(r["pe_ratio"], r["sector_median_pe"]),
        axis=1
    )

    # ---------- Final summary ----------
    summary = latest[[
        "company_key", "company_name", "broad_sector", "sub_sector",
        "pe_ratio", "pb_ratio", "market_cap_crore",
        "fcf_yield_pct", "sector_median_pe", "pe_vs_sector_median_pct",
        "pe_flag",
    ]].copy()

    summary = summary.rename(columns={
        "company_key":  "company_id",      # canonical ticker
        "broad_sector": "sector",
        "pe_ratio":     "P/E",
        "pb_ratio":     "P/B",
    })

    # ---------- Write Excel with proper sheet names ----------
    xlsx_path = OUTPUT_DIR / "valuation_summary.xlsx"
    caution  = summary[summary["pe_flag"] == "Caution"]
    discount = summary[summary["pe_flag"] == "Discount"]

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
        summary.to_excel(w,  sheet_name="Summary",  index=False)
        caution.to_excel(w,  sheet_name="Caution",  index=False)
        discount.to_excel(w, sheet_name="Discount", index=False)

    print(f"✅ Wrote {xlsx_path}")
    print(f"   Summary:  {len(summary)} rows")
    print(f"   Caution:  {len(caution)} rows")
    print(f"   Discount: {len(discount)} rows")

    # ---------- Write CSV of flagged companies ----------
    flags_csv = OUTPUT_DIR / "valuation_flags.csv"
    flagged = summary[summary["pe_flag"].isin(["Caution", "Discount"])]
    flagged.to_csv(flags_csv, index=False)
    print(f"✅ Wrote {flags_csv} ({len(flagged)} rows)")

    # ---------- Persist to SQLite ----------
    with sqlite3.connect(str(DB_PATH)) as c:
        summary.to_sql("valuation", c, if_exists="replace", index=False)
    print(f"✅ Persisted to DB: 'valuation' table")

    return summary


if __name__ == "__main__":
    run()