"""
src/analytics/cluster_profiling.py
Profiling, correlation heatmap, outliers, portfolio stats.
"""
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
REPORTS_DIR = ROOT / "reports"

KPIS = [
    "return_on_equity_pct", "return_on_capital_employed_pct",
    "net_profit_margin_pct", "operating_profit_margin_pct",
    "debt_to_equity", "interest_coverage",
    "pe_ratio", "pb_ratio", "dividend_yield_pct",
    "revenue_cagr_5yr",
]


def load_latest():
    conn = sqlite3.connect(str(DB_PATH))
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    sectors = pd.read_sql(
        "SELECT ticker, broad_sector FROM sectors", conn)
    conn.close()

    sectors = sectors.rename(columns={"ticker": "company_id"})
    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

    latest = (ratios.sort_values("year")
                    .groupby("company_id", as_index=False)
                    .tail(1))
    latest = latest.merge(sectors, on="company_id", how="left")
    return latest


def correlation_heatmap(df):
    avail = [k for k in KPIS if k in df.columns]
    corr = df[avail].apply(pd.to_numeric, errors="coerce").corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, square=True, cbar_kws={"shrink": 0.7})
    plt.title("KPI Correlation Matrix (Latest Year)")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "correlation_heatmap.png", dpi=120)
    plt.close()
    print(f"✅ Wrote {REPORTS_DIR / 'correlation_heatmap.png'}")


def outlier_report(df):
    rows = []
    for sector, grp in df.groupby("broad_sector"):
        for kpi in KPIS:
            if kpi not in grp.columns:
                continue
            vals = pd.to_numeric(grp[kpi], errors="coerce")
            mu, sd = vals.mean(), vals.std()
            if sd == 0 or pd.isna(sd):
                continue
            z = (vals - mu) / sd
            for cid, zval in zip(grp["company_id"], z):
                if pd.notna(zval) and abs(zval) > 3:
                    rows.append({
                        "company_id": cid,
                        "sector": sector,
                        "metric": kpi,
                        "value": float(vals.loc[grp["company_id"] == cid].iloc[0]),
                        "z_score": round(float(zval), 2),
                    })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "outlier_report.csv", index=False)
    print(f"✅ Wrote {OUTPUT_DIR / 'outlier_report.csv'} ({len(out)} rows)")


def portfolio_stats(df):
    rows = []
    for kpi in KPIS:
        if kpi not in df.columns:
            continue
        s = pd.to_numeric(df[kpi], errors="coerce").dropna()
        if s.empty:
            continue
        rows.append({
            "kpi": kpi,
            "P10": round(s.quantile(0.10), 2),
            "P25": round(s.quantile(0.25), 2),
            "P50": round(s.quantile(0.50), 2),
            "P75": round(s.quantile(0.75), 2),
            "P90": round(s.quantile(0.90), 2),
            "Mean": round(s.mean(), 2),
            "Std": round(s.std(), 2),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "portfolio_stats.csv", index=False)
    print(f"✅ Wrote {OUTPUT_DIR / 'portfolio_stats.csv'}")


def main():
    print("=" * 60)
    print("Day 37 — Cluster Profiling & Stats")
    print("=" * 60)

    df = load_latest()
    correlation_heatmap(df)
    outlier_report(df)
    portfolio_stats(df)


if __name__ == "__main__":
    main()
    