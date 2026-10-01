"""
src/reports/tearsheet.py
2-page company tearsheet PDF generator using ReportLab.

Fixed:
  - NaN handling in year_int (fixes ADANIGREEN, ATGL, LICI failures)
  - Charts wrapped in Table (fixes blank charts)
  - Cashflow loading uses proper numeric_id mapping
  - Deduplication of cashflow/bs rows
  - Larger chart sizes
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
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "tearsheets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Colors ----------
NAVY = colors.HexColor("#1E3A5F")
LIGHT_NAVY = colors.HexColor("#2C5282")
ACCENT = colors.HexColor("#E67E22")
GREEN = colors.HexColor("#2ECC71")
RED = colors.HexColor("#E74C3C")
LIGHT_GRAY = colors.HexColor("#F5F5F5")


# ==========================================================
# Data loading
# ==========================================================
def load_company_data(ticker: str) -> dict:
    conn = sqlite3.connect(str(DB_PATH))

    company = pd.read_sql(
        "SELECT ticker, company_name, company_id AS numeric_id "
        "FROM companies WHERE ticker = ?",
        conn, params=[ticker])

    sector = pd.read_sql(
        "SELECT broad_sector, sub_sector FROM sectors WHERE ticker = ?",
        conn, params=[ticker])

    ratios = pd.read_sql(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
        conn, params=[ticker])

    pl = pd.read_sql(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year_int",
        conn, params=[ticker])
    # Drop rows with NaN year_int
    pl = pl.dropna(subset=["year_int"]) if "year_int" in pl.columns else pl

    bs = pd.read_sql(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year_int",
        conn, params=[ticker])
    bs = bs.dropna(subset=["year_int"]) if "year_int" in bs.columns else bs
    bs = bs.sort_values("year_int").drop_duplicates(
        subset=["year_int"], keep="last").reset_index(drop=True)

    # Cashflow — map int ID, dedupe
    cf = pd.DataFrame()
    if not company.empty:
        numeric_id = int(company.iloc[0]["numeric_id"])
        cf = pd.read_sql(
            "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year_int",
            conn, params=[numeric_id])
        cf = cf.dropna(subset=["year_int"]) if "year_int" in cf.columns else cf
        cf = cf.sort_values("year_int").drop_duplicates(
            subset=["year_int"], keep="last").reset_index(drop=True)

    # Pros/cons
    pc = pd.DataFrame()
    pc_path = ROOT / "output" / "pros_cons_generated.csv"
    if pc_path.exists():
        pc_df = pd.read_csv(pc_path)
        pc = pc_df[pc_df["company_id"] == ticker]

    # Capital allocation
    allocation = "Unknown"
    alloc_path = ROOT / "output" / "capital_allocation.csv"
    if alloc_path.exists():
        alloc = pd.read_csv(alloc_path)
        match = alloc[alloc["company_id"] == ticker]
        if not match.empty:
            allocation = match.iloc[0]["capital_allocation_pattern"]

    conn.close()

    return {
        "ticker": ticker,
        "company_name": company.iloc[0]["company_name"] if not company.empty else ticker,
        "sector": sector.iloc[0]["broad_sector"] if not sector.empty else "—",
        "sub_sector": sector.iloc[0]["sub_sector"] if not sector.empty else "—",
        "ratios": ratios,
        "pl": pl,
        "bs": bs,
        "cf": cf,
        "pros_cons": pc,
        "allocation": allocation,
    }


# ==========================================================
# Charts
# ==========================================================
def make_bar_chart(years, v1, v2, color1, color2):
    d = Drawing(500, 200)
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 30
    chart.height = 150
    chart.width = 440

    v1 = [float(x) if pd.notna(x) else 0 for x in v1]
    v2 = [float(x) if pd.notna(x) else 0 for x in v2]

    chart.data = [v1, v2]
    chart.strokeColor = None
    chart.valueAxis.valueMin = min(0, min(v1 + v2) * 1.1) if (v1 + v2) else 0
    chart.valueAxis.valueMax = max(v1 + v2) * 1.15 if max(v1 + v2) > 0 else 1
    chart.valueAxis.valueStep = (chart.valueAxis.valueMax - chart.valueAxis.valueMin) / 5 or 1

    # 🔥 FIX: NaN-safe labels
    chart.categoryAxis.categoryNames = [
        str(int(y)) if pd.notna(y) else "—" for y in years
    ]
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = color1
    chart.bars[1].fillColor = color2
    chart.barWidth = 6
    chart.groupSpacing = 12

    d.add(chart)
    return d


def make_line_chart(years, v1, v2, color1, color2):
    d = Drawing(500, 200)
    chart = HorizontalLineChart()
    chart.x = 40
    chart.y = 30
    chart.height = 150
    chart.width = 440

    v1 = [float(x) if pd.notna(x) else 0 for x in v1]
    v2 = [float(x) if pd.notna(x) else 0 for x in v2]

    chart.data = [v1, v2]

    # 🔥 FIX: NaN-safe labels
    chart.categoryAxis.categoryNames = [
        str(int(y)) if pd.notna(y) else "—" for y in years
    ]
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 7
    chart.lines[0].strokeColor = color1
    chart.lines[0].strokeWidth = 2.5
    chart.lines[1].strokeColor = color2
    chart.lines[1].strokeWidth = 2.5
    chart.joinedLines = 1
    chart.valueAxis.valueMin = 0

    d.add(chart)
    return d


def _wrap_chart(chart):
    t = Table([[chart]], colWidths=[16 * cm], rowHeights=[6 * cm])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ==========================================================
# Page 1
# ==========================================================
def build_page_1(data, styles):
    elements = []

    header = Table(
        [[Paragraph(
            f'<b>{data["company_name"]}</b> &nbsp;<font size="14">({data["ticker"]})</font>',
            ParagraphStyle("h", parent=styles["Normal"],
                           textColor=colors.white, fontSize=18, leading=22)
        )]],
        colWidths=[17 * cm], rowHeights=[1.2 * cm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        f'<font size="9" color="#666666">Sector: {data["sector"]} '
        f'| Sub-Sector: {data["sub_sector"]}</font>',
        styles["Normal"]))
    elements.append(Spacer(1, 12))

    ratios = data["ratios"]
    if ratios.empty:
        elements.append(Paragraph("No ratio data available.", styles["Normal"]))
        elements.append(PageBreak())
        return elements

    latest = ratios.sort_values("year").iloc[-1]

    def fmt(v, suffix="", dec=1):
        if v is None or pd.isna(v):
            return "N/A"
        try:
            return f"{float(v):.{dec}f}{suffix}"
        except Exception:
            return "N/A"

    kpis = [
        ("ROE",      fmt(latest.get("return_on_equity_pct"), "%")),
        ("ROCE",     fmt(latest.get("return_on_capital_employed_pct"), "%")),
        ("NPM",      fmt(latest.get("net_profit_margin_pct"), "%")),
        ("D/E",      fmt(latest.get("debt_to_equity"), "", 2)),
        ("Rev CAGR", fmt(latest.get("revenue_cagr_5yr"), "%")),
        ("FCF",      fmt(latest.get("free_cash_flow_cr"), " Cr", 0)),
    ]

    def kpi_cell(label, value):
        return Paragraph(
            f'<font size="8" color="#666666">{label}</font><br/>'
            f'<font size="16" color="#1E3A5F"><b>{value}</b></font>',
            ParagraphStyle("k", parent=styles["Normal"], alignment=1))

    kpi_rows = [
        [kpi_cell(*kpis[0]), kpi_cell(*kpis[1]), kpi_cell(*kpis[2])],
        [kpi_cell(*kpis[3]), kpi_cell(*kpis[4]), kpi_cell(*kpis[5])],
    ]
    kpi_tbl = Table(kpi_rows, colWidths=[5.6 * cm] * 3, rowHeights=[1.5 * cm] * 2)
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(kpi_tbl)
    elements.append(Spacer(1, 15))

    # Revenue & Net Profit chart
    elements.append(Paragraph("<b>Revenue &amp; Net Profit (10-Year)</b>", styles["Heading3"]))
    pl10 = data["pl"].tail(10)
    pl10 = pl10.dropna(subset=["year_int"]) if "year_int" in pl10.columns else pl10
    if not pl10.empty and "sales" in pl10.columns:
        years = pl10["year_int"].tolist()
        rev = pl10["sales"].tolist()
        pat = pl10["net_profit"].tolist()
        elements.append(_wrap_chart(make_bar_chart(years, rev, pat, NAVY, ACCENT)))

        legend = Table([[
            Paragraph('<font color="#1E3A5F">■ Revenue (Cr)</font>', styles["Normal"]),
            Paragraph('<font color="#E67E22">■ Net Profit (Cr)</font>', styles["Normal"]),
        ]], colWidths=[4 * cm] * 2)
        elements.append(legend)
    else:
        elements.append(Paragraph("No P&L data available.", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # ROE & ROCE chart
    elements.append(Paragraph("<b>ROE &amp; ROCE Trend (10-Year)</b>", styles["Heading3"]))
    r10 = data["ratios"].tail(10)
    if not r10.empty:
        years = r10["year"].tolist()
        roe = r10["return_on_equity_pct"].tolist()
        roce = r10["return_on_capital_employed_pct"].tolist()
        elements.append(_wrap_chart(make_line_chart(years, roe, roce, GREEN, ACCENT)))

        legend = Table([[
            Paragraph('<font color="#2ECC71">▬ ROE (%)</font>', styles["Normal"]),
            Paragraph('<font color="#E67E22">▬ ROCE (%)</font>', styles["Normal"]),
        ]], colWidths=[4 * cm] * 2)
        elements.append(legend)

    elements.append(PageBreak())
    return elements


# ==========================================================
# Page 2
# ==========================================================
def build_page_2(data, styles):
    elements = []

    elements.append(Paragraph(
        f'<b>{data["company_name"]}</b> &nbsp;<font size="11">({data["ticker"]})</font>',
        styles["Heading2"]))
    elements.append(Spacer(1, 10))

    # Balance Sheet
    elements.append(Paragraph("<b>Balance Sheet Composition</b>", styles["Heading3"]))
    bs10 = data["bs"].tail(10)
    bs10 = bs10.dropna(subset=["year_int"]) if "year_int" in bs10.columns else bs10
    if not bs10.empty and "total_assets" in bs10.columns:
        years = bs10["year_int"].tolist()
        assets = bs10["total_assets"].tolist()
        liab = bs10["total_liabilities"].tolist()
        elements.append(_wrap_chart(make_bar_chart(years, assets, liab, NAVY, RED)))
    else:
        elements.append(Paragraph("No balance sheet data.", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # Cash Flow table
    elements.append(Paragraph("<b>Cash Flow (Latest Year)</b>", styles["Heading3"]))
    cf = data["cf"]
    if not cf.empty:
        latest_cf = cf.iloc[-1]
        cfo = latest_cf.get("operating_cashflow", 0) or 0
        cfi = latest_cf.get("investing_cashflow", 0) or 0
        cff = latest_cf.get("financing_cashflow", 0) or 0
        net = cfo + cfi + cff

        cf_rows = [
            ["Item", "Value (Cr)"],
            ["Operating (CFO)", f"{cfo:,.0f}"],
            ["Investing (CFI)", f"{cfi:,.0f}"],
            ["Financing (CFF)", f"{cff:,.0f}"],
            ["Net Cash Flow", f"{net:,.0f}"],
        ]
        cf_tbl = Table(cf_rows, colWidths=[8 * cm, 8 * cm])
        cf_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 4), (-1, 4), LIGHT_GRAY),
            ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(cf_tbl)
    else:
        elements.append(Paragraph("No cash flow data.", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # Capital allocation badge
    badge = Table(
        [[Paragraph(
            f'<b>Capital Allocation Pattern:</b> {data["allocation"]}',
            ParagraphStyle("b", parent=styles["Normal"],
                           textColor=colors.white, fontSize=11))]],
        colWidths=[17 * cm], rowHeights=[0.8 * cm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(badge)
    elements.append(Spacer(1, 15))

    # Pros & Cons
    elements.append(Paragraph("<b>Pros &amp; Cons</b>", styles["Heading3"]))
    pc = data["pros_cons"]
    if not pc.empty:
        pros = pc[pc["type"] == "pro"]["text"].head(5).tolist()
        cons = pc[pc["type"] == "con"]["text"].head(5).tolist()

        elements.append(Paragraph(
            '<font color="#2ECC71"><b>✓ Pros</b></font>', styles["Normal"]))
        if pros:
            for p in pros:
                elements.append(Paragraph(f"• {p}", styles["Normal"]))
        else:
            elements.append(Paragraph("<i>No pros available.</i>", styles["Normal"]))

        elements.append(Spacer(1, 8))

        elements.append(Paragraph(
            '<font color="#E74C3C"><b>✗ Cons</b></font>', styles["Normal"]))
        if cons:
            for c in cons:
                elements.append(Paragraph(f"• {c}", styles["Normal"]))
        else:
            elements.append(Paragraph("<i>No cons available.</i>", styles["Normal"]))
    else:
        elements.append(Paragraph("No pros/cons data.", styles["Normal"]))

    return elements


# ==========================================================
# Main
# ==========================================================
def generate_tearsheet(ticker: str, output_path: str) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[tearsheet] Generating {ticker} → {output_path.name}")

    data = load_company_data(ticker)
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=f"{data['company_name']} ({ticker})",
    )

    elements = []
    elements.extend(build_page_1(data, styles))
    elements.extend(build_page_2(data, styles))

    doc.build(elements)
    size_kb = output_path.stat().st_size / 1024
    print(f"✅ Wrote {output_path.name} ({size_kb:.1f} KB)")

    return str(output_path)


if __name__ == "__main__":
    TEST_TICKERS = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]

    for t in TEST_TICKERS:
        try:
            generate_tearsheet(t, OUTPUT_DIR / f"{t}_tearsheet.pdf")
        except Exception as e:
            import traceback
            print(f"❌ Failed for {t}: {e}")
            traceback.print_exc()