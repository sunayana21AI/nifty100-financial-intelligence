"""
src/analytics/pattern_changes.py
Capital Allocation Pattern Changes Report.

For each company, classifies capital allocation pattern for every year
(based on sign of CFO, CFI, CFF) and identifies year-over-year changes.

Detects:
  - Improvement:   e.g. Distress Signal → Reinvestor
  - Deterioration: e.g. Reinvestor → Distress Signal
  - Neutral:       e.g. Reinvestor → Cash Accumulator

Writes: output/pattern_changes.csv
        output/capital_allocation.csv (latest year snapshot per company)
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ==========================================================
# Pattern classification
# ==========================================================
def classify_pattern(cfo, cfi, cff):
    """Classify into 8 capital allocation patterns based on signs."""
    if any(x is None for x in (cfo, cfi, cff)):
        return "Unknown"
    try:
        if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
            return "Unknown"
    except Exception:
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
# Pattern change type
# ==========================================================
# Rank of patterns from best to worst
PATTERN_RANK = {
    "Reinvestor":               1,   # Best — funds growth internally
    "Cash Accumulator":         2,
    "Divestment & Deleverage":  3,
    "Growth Funded by Debt":    4,
    "Turnaround":               5,
    "Liquidation Mode":         6,
    "Distress Signal":          7,
    "Severe Distress":          8,   # Worst
    "Unknown":                  9,
    "Other":                    9,
}


def change_type(prev, curr):
    """Classify the change as Improvement / Deterioration / Neutral."""
    r_prev = PATTERN_RANK.get(prev, 9)
    r_curr = PATTERN_RANK.get(curr, 9)

    if r_curr < r_prev:
        return "Improvement"
    if r_curr > r_prev:
        return "Deterioration"
    return "Neutral"


# ==========================================================
# Main
# ==========================================================
def build_pattern_history():
    """Build year-wise capital allocation patterns for all companies."""
    print(f"[pattern_changes] Reading from: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    companies = pd.read_sql(
        "SELECT ticker, company_id AS numeric_id, company_name FROM companies", conn)
    sectors = pd.read_sql(
        "SELECT ticker, broad_sector FROM sectors", conn)
    conn.close()

    # Map cashflow int ID → ticker
    companies["numeric_id"] = pd.to_numeric(
        companies["numeric_id"], errors="coerce")
    id_to_ticker = dict(zip(companies["numeric_id"], companies["ticker"]))

    def resolve(x):
        try:
            n = pd.to_numeric(x, errors="coerce")
            if pd.notna(n) and n in id_to_ticker:
                return id_to_ticker[n]
            return str(x).strip()
        except Exception:
            return str(x).strip()

    cf["company_id"] = cf["company_id"].apply(resolve)

    # Normalize year
    if "year_int" in cf.columns:
        cf["year"] = pd.to_numeric(cf["year_int"], errors="coerce")
    else:
        cf["year"] = pd.to_numeric(cf["year"], errors="coerce")

    cf["company_id"] = cf["company_id"].astype(str).str.strip()

    # Valid companies only
    valid = set(companies["ticker"].astype(str).str.strip())
    cf = cf[cf["company_id"].isin(valid)].copy()

    # Classify pattern per row
    def _classify(row):
        cfo = row.get("operating_cashflow")
        cfi = row.get("investing_cashflow")
        cff = row.get("financing_cashflow")
        try:
            if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
                return "Unknown"
        except Exception:
            return "Unknown"
        return classify_pattern(float(cfo), float(cfi), float(cff))

    cf["pattern"] = cf.apply(_classify, axis=1)
        # ---------- Deduplicate: keep last row per (company_id, year) ----------
    cf = cf.sort_values("year").drop_duplicates(
        subset=["company_id", "year"], keep="last"
    ).copy()

    # Sector map
    sectors = sectors.rename(columns={"ticker": "company_id"})
    sectors["company_id"] = sectors["company_id"].astype(str).str.strip()
    cf = cf.merge(
        sectors[["company_id", "broad_sector"]],
        on="company_id", how="left"
    )

    # Company name map
    comp_map = companies.set_index("ticker")["company_name"].to_dict()
    cf["company_name"] = cf["company_id"].map(comp_map)

    return cf, companies, sectors


def compute_pattern_changes(cf):
    """Compare each year's pattern with previous year's pattern."""
    rows = []

    for cid, group in cf.groupby("company_id"):
        group = group.sort_values("year")
        if len(group) < 2:
            continue

        prev = None
        for _, row in group.iterrows():
            curr = row["pattern"]

            if prev is not None and prev != curr and curr != "Unknown" and prev != "Unknown":
                rows.append({
                    "company_id":     cid,
                    "company_name":   row.get("company_name"),
                    "sector":         row.get("broad_sector"),
                    "year":           int(row["year"]) if pd.notna(row["year"]) else None,
                    "prev_pattern":   prev,
                    "curr_pattern":   curr,
                    "change_type":    change_type(prev, curr),
                })

            prev = curr

    df = pd.DataFrame(rows)
    return df


def build_latest_snapshot(cf):
    """Latest year pattern per company."""
    latest = (cf.sort_values("year")
                .groupby("company_id", as_index=False)
                .tail(1))
    return latest[[
        "company_id", "company_name", "broad_sector",
        "year", "pattern",
        "operating_cashflow", "investing_cashflow", "financing_cashflow"
    ]].rename(columns={
        "broad_sector": "sector",
        "year": "latest_year",
        "pattern": "capital_allocation_pattern",
    })


def main():
    cf, companies, sectors = build_pattern_history()

    # ---------- 1. Latest year snapshot (capital_allocation.csv) ----------
    snapshot = build_latest_snapshot(cf)
    snap_path = OUTPUT_DIR / "capital_allocation.csv"
    snapshot.to_csv(snap_path, index=False)
    print(f"✅ Wrote {snap_path} ({len(snapshot)} rows)")

    # ---------- 2. Pattern distribution summary ----------
    print(f"\n[pattern_changes] Pattern distribution (latest year):")
    counts = snapshot["capital_allocation_pattern"].value_counts()
    for pattern, count in counts.items():
        print(f"   {pattern:30s} {count}")

    # ---------- 3. YoY pattern changes ----------
    changes = compute_pattern_changes(cf)
    changes_path = OUTPUT_DIR / "pattern_changes.csv"
    changes.to_csv(changes_path, index=False)
    print(f"\n✅ Wrote {changes_path} ({len(changes)} rows)")

    if not changes.empty:
        print(f"\n[pattern_changes] Change type breakdown:")
        print(f"   {changes['change_type'].value_counts().to_dict()}")

        print(f"\n[pattern_changes] Top 10 recent changes:")
        recent = changes.sort_values("year", ascending=False).head(10)
        print(recent[[
            "company_id", "year", "prev_pattern",
            "curr_pattern", "change_type"
        ]].to_string(index=False))

    return snapshot, changes


if __name__ == "__main__":
    main()