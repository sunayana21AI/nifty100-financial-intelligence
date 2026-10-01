"""
src/reports/portfolio_summary.py
Portfolio Summary PDF — one page per company (alphabetical order).
"""
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "portfolio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#1E3A5F")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
GRAY = colors.HexColor("#95A5A6")

# Hex color strings (for HTML font tags)
GREEN_HEX = "#2ECC71"
RED_HEX = "#E74C3C"
GRAY_HEX = "#95A5A6"


def load_all_data():
    conn = sqlite3.connect(str(DB_PATH))
    companies = pd.read_sql(
        "SELECT ticker, company_name FROM companies ORDER BY ticker", conn)
    sectors = pd.read_sql(
        "SELECT ticker, broad_sector FROM sectors", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    conn.close()

    companies["ticker"] = companies["ticker"].astype(str).str.strip()
    sectors["ticker"] = sectors["ticker"].astype(str).str.strip()
    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

    ratios = ratios.sort_values(["company_id", "year"])
    companies = companies.merge(sectors, on="ticker", how="left")
    return companies, ratios


def trend_arrow(curr, prev, threshold=2.0):
    """Return (arrow, hex_color_string_with_hash)."""
    if prev is None or pd.isna(prev) or pd.isna(curr) or prev == 0:
        return "→", GRAY_HEX
    change_pct = (curr - prev) / abs(prev) * 100
    if change_pct > threshold:
        return "↑", GREEN_HEX
    if change_pct < -threshold:
        return "↓", RED_HEX
    return "→", GRAY_HEX


def get_metric_pair(ratios_ticker, col):
    if col not in ratios_ticker.columns:
        return None, None
    s = pd.to_numeric(ratios_ticker[col], errors="coerce").dropna()
    if len(s) < 1:
        return None, None
    latest = float(s.iloc[-1])
    prev = float(s.iloc[-2]) if len(s) >= 2 else None
    return latest, prev


def build_company_page(company_row, ratios_ticker, styles):
    elements = []

    header = Table(
        [[Paragraph(
            f'<b>{company_row["company_name"]}</b> &nbsp;<font size="12">({company_row["ticker"]})</font>',
            ParagraphStyle("h", parent=styles["Normal"],
                           textColor=colors.white, fontSize=16, leading=20))]],
        colWidths=[17 * cm], rowHeights=[1.1 * cm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 4))

    sector = company_row.get("broad_sector", "—")
    elements.append(Paragraph(
        f'<font size="9" color="#666666">Sector: {sector}</font>',
        styles["Normal"]))
    elements.append(Spacer(1, 12))

    metrics = [
        ("ROE",       "return_on_equity_pct",              "%", 1),
        ("ROCE",      "return_on_capital_employed_pct",    "%", 1),
        ("NPM",       "net_profit_margin_pct",             "%", 1),
        ("D/E",       "debt_to_equity",                    "",  2),
        ("Rev CAGR",  "revenue_cagr_5yr",                  "%", 1),
        ("FCF",       "free_cash_flow_cr",                 " Cr", 0),
    ]

    def kpi_cell(label, col, suffix, dec):
        latest, prev = get_metric_pair(ratios_ticker, col)

        if latest is None:
            val_str = "N/A"
            arrow, arrow_color = "→", GRAY_HEX
        else:
            try:
                val_str = f"{latest:.{dec}f}{suffix}"
            except Exception:
                val_str = "N/A"
            arrow, arrow_color = trend_arrow(latest, prev)

        # 🔥 FIX: arrow_color is now a "#RRGGBB" string
        return Paragraph(
            f'<font size="8" color="#666666">{label}</font><br/>'
            f'<font size="15" color="#1E3A5F"><b>{val_str}</b></font> '
            f'<font size="14" color="{arrow_color}">{arrow}</font>',
            ParagraphStyle("k", parent=styles["Normal"], alignment=1))

    kpi_rows = [
        [kpi_cell(*metrics[0]), kpi_cell(*metrics[1]), kpi_cell(*metrics[2])],
        [kpi_cell(*metrics[3]), kpi_cell(*metrics[4]), kpi_cell(*metrics[5])],
    ]
    kpi_tbl = Table(kpi_rows, colWidths=[5.6 * cm] * 3, rowHeights=[1.6 * cm] * 2)
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(kpi_tbl)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        '<font size="8" color="#999999">'
        '↑ improved vs prior year &nbsp;|&nbsp; '
        '↓ declined vs prior year &nbsp;|&nbsp; '
        '→ flat within ±2%'
        '</font>',
        styles["Normal"]))

    elements.append(PageBreak())
    return elements


def main():
    print("=" * 60)
    print("Day 35 — Portfolio Summary PDF")
    print("=" * 60)

    companies, ratios = load_all_data()
    print(f"Total companies: {len(companies)}")

    output_path = OUTPUT_DIR / "portfolio_summary.pdf"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title="Nifty 100 Portfolio Summary",
    )

    elements = []

    # Cover page
    elements.append(Spacer(1, 5 * cm))
    elements.append(Paragraph(
        '<b>Nifty 100 — Portfolio Summary</b>',
        ParagraphStyle("cover", parent=styles["Normal"],
                       fontSize=28, textColor=NAVY, alignment=1)))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(
        f'Total Companies: <b>{len(companies)}</b>',
        ParagraphStyle("c2", parent=styles["Normal"],
                       fontSize=14, alignment=1)))
    elements.append(PageBreak())

    companies_sorted = companies.sort_values("ticker")

    for i, (_, company_row) in enumerate(companies_sorted.iterrows(), 1):
        ticker = company_row["ticker"]
        ratios_ticker = ratios[ratios["company_id"] == ticker]
        if ratios_ticker.empty:
            continue
        try:
            elements.extend(build_company_page(company_row, ratios_ticker, styles))
            print(f"[{i}/{len(companies)}] ✅ {ticker}")
        except Exception as e:
            print(f"[{i}/{len(companies)}] ❌ {ticker}: {e}")

    doc.build(elements)
    size_kb = output_path.stat().st_size / 1024
    print(f"\n✅ Wrote {output_path}")
    print(f"   Size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()