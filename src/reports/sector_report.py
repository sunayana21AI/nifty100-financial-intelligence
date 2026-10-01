"""
src/reports/sector_report.py
Generate 11 sector-level PDF reports.
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "sector"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#1E3A5F")
LIGHT_GRAY = colors.HexColor("#F5F5F5")


def load_sector_data():
    conn = sqlite3.connect(str(DB_PATH))
    sectors = pd.read_sql("SELECT ticker, broad_sector, sub_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT ticker, company_name FROM companies", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    conn.close()

    sectors["ticker"] = sectors["ticker"].astype(str).str.strip()
    companies["ticker"] = companies["ticker"].astype(str).str.strip()
    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

    latest = (ratios.sort_values("year")
                    .groupby("company_id", as_index=False)
                    .tail(1))

    df = latest.merge(companies, left_on="company_id", right_on="ticker", how="left")
    df = df.merge(sectors, on="ticker", how="left")
    return df


def build_sector_pdf(sector_name, sector_df, output_path):
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=f"Sector Report: {sector_name}",
    )

    elements = []

    # Header
    header = Table(
        [[Paragraph(f'<b>{sector_name}</b> — Sector Report',
                    ParagraphStyle("h", parent=styles["Normal"],
                                   textColor=colors.white, fontSize=18))]],
        colWidths=[18 * cm], rowHeights=[1.2 * cm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    # Summary
    elements.append(Paragraph("<b>Sector Summary</b>", styles["Heading3"]))
    n = sector_df["company_id"].nunique()

    def med(col):
        if col not in sector_df.columns:
            return None
        s = pd.to_numeric(sector_df[col], errors="coerce").dropna()
        return float(s.median()) if not s.empty else None

    def fmt(v, suffix="", dec=1):
        if v is None or pd.isna(v):
            return "N/A"
        return f"{v:.{dec}f}{suffix}"

    summary_rows = [
        ["Metric", "Median"],
        ["Companies", str(n)],
        ["Median ROE (%)", fmt(med("return_on_equity_pct"))],
        ["Median ROCE (%)", fmt(med("return_on_capital_employed_pct"))],
        ["Median NPM (%)", fmt(med("net_profit_margin_pct"))],
        ["Median P/E", fmt(med("pe_ratio"), "x")],
        ["Median D/E", fmt(med("debt_to_equity"), "", 2)],
        ["Median Rev CAGR 5yr (%)", fmt(med("revenue_cagr_5yr"))],
    ]

    summary_tbl = Table(summary_rows, colWidths=[8 * cm, 5 * cm])
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_tbl)
    elements.append(Spacer(1, 15))

    # Company table
    elements.append(Paragraph("<b>Companies in Sector</b>", styles["Heading3"]))

    cols = [
        ("Ticker", "company_id", ""),
        ("ROE%", "return_on_equity_pct", "%"),
        ("ROCE%", "return_on_capital_employed_pct", "%"),
        ("NPM%", "net_profit_margin_pct", "%"),
        ("P/E", "pe_ratio", "x"),
        ("P/B", "pb_ratio", "x"),
        ("D/E", "debt_to_equity", ""),
        ("Rev CAGR", "revenue_cagr_5yr", "%"),
    ]

    table_data = [[c[0] for c in cols]]

    for _, row in sector_df.sort_values("company_id").iterrows():
        row_data = [str(row["company_id"])]
        for _, col, suffix in cols[1:]:
            val = row.get(col)
            if pd.isna(val):
                row_data.append("—")
            else:
                try:
                    row_data.append(f"{float(val):.1f}{suffix}")
                except Exception:
                    row_data.append("—")
        table_data.append(row_data)

    table_data = table_data[:35]

    company_tbl = Table(table_data, colWidths=[2.5 * cm] + [2 * cm] * 7, repeatRows=1)
    company_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(company_tbl)

    doc.build(elements)
    size_kb = output_path.stat().st_size / 1024
    print(f"✅ Wrote {output_path.name} ({size_kb:.1f} KB, {n} companies)")


def main():
    print("=" * 60)
    print("Day 34 — Sector Reports Generation")
    print("=" * 60)

    df = load_sector_data()
    sectors = sorted(df["broad_sector"].dropna().unique())
    print(f"Total sectors: {len(sectors)}\n")

    for sec in sectors:
        sec_df = df[df["broad_sector"] == sec]
        safe_name = str(sec).replace(" ", "_").replace("&", "and")
        output = OUTPUT_DIR / f"{safe_name}_report.pdf"
        try:
            build_sector_pdf(sec, sec_df, output)
        except Exception as e:
            import traceback
            print(f"❌ FAILED {sec}: {e}")
            traceback.print_exc()

    pdf_files = list(OUTPUT_DIR.glob("*.pdf"))
    print(f"\n📄 Total sector PDFs: {len(pdf_files)}")


if __name__ == "__main__":
    main()