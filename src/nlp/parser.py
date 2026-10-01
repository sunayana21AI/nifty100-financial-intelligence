"""
src/nlp/parser.py
Parse analysis.xlsx text fields using regex to extract CAGR values.

File structure (IMPORTANT):
  Row 0: Title row  ("Bluestock Fintech — Nifty 100 | Analysis | 20 records")
  Row 1: Actual header  (id, company_id, compounded_sales_growth, ...)
  Row 2+: Data

So we use skiprows=1 to skip the title row.

Target: fields like "10 Years: 21%" → period=10, value=21.0
Also handles: "5 Years       24%", "10Years: 22%", "10 Years:     15%"
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "analysis.xlsx"
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------- Regex ----------
# Handles: "10 Years: 21%", "10Years: 22%", "5 Years       24%",
#          "10 Years:     15%", "5 Years          14%"
PATTERN = re.compile(r"(\d+)\s*Years?\s*:?\s*([\d.]+)\s*%")

# Fields to parse from the analysis file
TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


def parse_analysis_text() -> pd.DataFrame:
    """Parse analysis.xlsx and extract CAGR values."""
    print(f"[parser] Reading: {DATA_PATH}")

    if not DATA_PATH.exists():
        print(f"❌ File not found: {DATA_PATH}")
        return pd.DataFrame()

    # 🔥 KEY FIX: skiprows=1 to skip the title row
    df = pd.read_excel(DATA_PATH, skiprows=1)

    # Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"[parser] Columns found: {df.columns.tolist()}")
    print(f"[parser] Rows loaded: {len(df)}")

    parsed_rows = []
    failed_rows = []

    for _, row in df.iterrows():
        company_id = row.get("company_id") or row.get("ticker")
        if pd.isna(company_id):
            continue
        company_id = str(company_id).strip()

        for field in TARGET_FIELDS:
            if field not in df.columns:
                continue
            if pd.isna(row[field]):
                continue

            text = str(row[field]).strip()
            matches = PATTERN.findall(text)

            if matches:
                for period, value in matches:
                    parsed_rows.append({
                        "company_id": company_id,
                        "metric_type": field,
                        "period_years": int(period),
                        "value_pct": float(value),
                    })
            else:
                failed_rows.append({
                    "company_id": company_id,
                    "metric_type": field,
                    "raw_text": text,
                })

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=["company_id", "metric_type", "period_years", "value_pct"],
    )
    failures_df = pd.DataFrame(
        failed_rows,
        columns=["company_id", "metric_type", "raw_text"],
    )

    # Always write CSVs (even if empty, with headers — prevents EmptyDataError)
    parsed_df.to_csv(OUTPUT_DIR / "analysis_parsed.csv", index=False)
    failures_df.to_csv(OUTPUT_DIR / "parse_failures.csv", index=False)

    print(f"✅ Parsed {len(parsed_df)} values")
    print(f"⚠️  Failed to parse {len(failures_df)} entries")

    if not parsed_df.empty:
        print(f"\n[parser] Sample parsed values:")
        print(parsed_df.head(10).to_string(index=False))

    if not failures_df.empty:
        print(f"\n[parser] Sample failures:")
        print(failures_df.head(5).to_string(index=False))

    return parsed_df


def cross_validate_cagr() -> list[dict]:
    """Compare parsed CAGR vs computed CAGR — flag divergence > 5%."""
    parsed_path = OUTPUT_DIR / "analysis_parsed.csv"

    if not parsed_path.exists() or parsed_path.stat().st_size < 10:
        print("⚠️  No parsed data — skipping cross-validation")
        return []

    parsed = pd.read_csv(parsed_path)

    if parsed.empty:
        print("⚠️  Parsed CSV is empty — skipping cross-validation")
        return []

    conn = sqlite3.connect(str(DB_PATH))
    computed = pd.read_sql("""
        SELECT company_id, revenue_cagr_5yr, pat_cagr_5yr, eps_cagr_5yr
        FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    conn.close()

    # Map analysis field → DB column
    metric_map = {
        "compounded_sales_growth":  "revenue_cagr_5yr",
        "compounded_profit_growth": "pat_cagr_5yr",
    }

    divergences = []
    for _, p in parsed.iterrows():
        # Only compare 5-year CAGRs (matches DB columns)
        if p["period_years"] != 5:
            continue

        metric = metric_map.get(p["metric_type"])
        if not metric:
            continue

        c = computed[computed["company_id"] == p["company_id"]]
        if c.empty:
            continue

        computed_val = c.iloc[0][metric]
        if pd.isna(computed_val):
            continue

        # Divergence as % of computed value
        denom = max(abs(computed_val), 1.0)
        diff_pct = abs(p["value_pct"] - computed_val) / denom * 100

        if diff_pct > 5:
            divergences.append({
                "company_id": p["company_id"],
                "metric_type": p["metric_type"],
                "parsed_value": round(p["value_pct"], 2),
                "computed_value": round(float(computed_val), 2),
                "divergence_pct": round(diff_pct, 2),
            })

    div_df = pd.DataFrame(
        divergences,
        columns=["company_id", "metric_type", "parsed_value",
                 "computed_value", "divergence_pct"],
    )
    div_df.to_csv(OUTPUT_DIR / "cagr_divergences.csv", index=False)

    print(f"\n⚠️  Found {len(div_df)} divergences > 5%")
    if not div_df.empty:
        print(div_df.to_string(index=False))

    return divergences


def main():
    parsed = parse_analysis_text()
    if not parsed.empty:
        cross_validate_cagr()
    else:
        print("\n⚠️  No values parsed — skipping cross-validation")


if __name__ == "__main__":
    main()