"""
src/reports/batch_generate.py
Batch generate 92 tearsheets for all companies.

- Loads all tickers from companies table
- Skips companies with < 3 years of data
- Logs skipped tickers to output/skipped_tearsheets.csv
- Generates PDFs into reports/tearsheets/

Usage:
    python src/reports/batch_generate.py
"""
import sqlite3
import sys
import traceback
from pathlib import Path

import pandas as pd

# Add project root
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from reports.tearsheet import generate_tearsheet, DB_PATH, OUTPUT_DIR


def load_all_tickers():
    """Get all tickers from companies table."""
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql(
        "SELECT ticker FROM companies WHERE ticker IS NOT NULL ORDER BY ticker",
        conn)
    conn.close()
    return df["ticker"].astype(str).str.strip().tolist()


def count_years_for_ticker(ticker: str) -> int:
    """Count distinct years of data in financial_ratios."""
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql(
        "SELECT COUNT(DISTINCT year) AS n FROM financial_ratios WHERE company_id = ?",
        conn, params=[ticker])
    conn.close()
    return int(df.iloc[0]["n"]) if not df.empty else 0


def main():
    print("=" * 60)
    print("Day 34 — Batch Tearsheet Generation")
    print("=" * 60)

    tickers = load_all_tickers()
    print(f"Total companies: {len(tickers)}")
    print()

    generated = []
    skipped = []
    failed = []

    for i, ticker in enumerate(tickers, 1):
        # Check data sufficiency
        n_years = count_years_for_ticker(ticker)

        if n_years < 3:
            skipped.append({
                "ticker": ticker,
                "reason": f"Only {n_years} years of data (<3)",
                "years": n_years,
            })
            print(f"[{i}/{len(tickers)}] SKIP {ticker} ({n_years} yrs)")
            continue

        # Try to generate
        try:
            pdf_path = OUTPUT_DIR / f"{ticker}_tearsheet.pdf"
            generate_tearsheet(ticker, str(pdf_path))
            generated.append(ticker)
        except Exception as e:
            failed.append({
                "ticker": ticker,
                "error": str(e)[:200],
            })
            print(f"[{i}/{len(tickers)}] ❌ FAILED {ticker}: {e}")
            traceback.print_exc()

    # ---------- Summary ----------
    print()
    print("=" * 60)
    print("BATCH SUMMARY")
    print("=" * 60)
    print(f"✅ Generated:  {len(generated)}")
    print(f"⏭️  Skipped:    {len(skipped)}")
    print(f"❌ Failed:     {len(failed)}")

    # ---------- Save logs ----------
    if skipped:
        skip_df = pd.DataFrame(skipped)
        skip_path = ROOT / "output" / "skipped_tearsheets.csv"
        skip_df.to_csv(skip_path, index=False)
        print(f"\n📝 Skipped log: {skip_path}")
        print(skip_df.to_string(index=False))

    if failed:
        fail_df = pd.DataFrame(failed)
        fail_path = ROOT / "output" / "failed_tearsheets.csv"
        fail_df.to_csv(fail_path, index=False)
        print(f"\n⚠️  Failed log: {fail_path}")

    # ---------- Verify count ----------
    pdf_files = list(OUTPUT_DIR.glob("*_tearsheet.pdf"))
    print(f"\n📄 PDF files in {OUTPUT_DIR}: {len(pdf_files)}")

    return generated, skipped, failed


if __name__ == "__main__":
    main()