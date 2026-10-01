"""
src/analytics/clustering.py
KMeans clustering of companies into 5 archetypes.

Fixes:
  - Filter to valid companies from master table (92, not 100)
  - Realistic outlier caps (ROE: -50 to +50)
  - Impute missing values with sector median
  - Smarter cluster naming (no duplicates)
"""
import sqlite3
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
REPORTS_DIR = ROOT / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

RANDOM_STATE = 42
N_CLUSTERS = 5

# Realistic caps — prevents outliers from distorting KMeans
CAPS = {
    "return_on_equity_pct":         (-50, 50),
    "debt_to_equity":               (-2, 5),
    "revenue_cagr_5yr":             (-30, 60),
    "fcf_cagr_5yr":                 (-50, 80),
    "operating_profit_margin_pct":  (-30, 60),
}


# ==========================================================
# Data loading
# ==========================================================
def load_features():
    """Load latest-year features per company (only valid companies)."""
    conn = sqlite3.connect(str(DB_PATH))
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    sectors = pd.read_sql(
        "SELECT ticker, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT ticker FROM companies", conn)
    conn.close()

    sectors = sectors.rename(columns={"ticker": "company_id"})
    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    sectors["company_id"] = sectors["company_id"].astype(str).str.strip()
    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

    # Latest year per company
    latest = (ratios.sort_values("year")
                    .groupby("company_id", as_index=False)
                    .tail(1))

    # Merge sector
    latest = latest.merge(sectors, on="company_id", how="left")

    # 🔥 Filter to valid companies only (excludes 8 orphans)
    valid_tickers = set(companies["ticker"].astype(str).str.strip())
    latest = latest[latest["company_id"].isin(valid_tickers)].copy()

    # Ensure all features present
    for feat in FEATURES:
        if feat not in latest.columns:
            latest[feat] = np.nan

    return latest


def compute_fcf_cagr_5yr(df):
    """Add fcf_cagr_5yr if missing — compute from free_cash_flow_cr."""
    if "fcf_cagr_5yr" in df.columns and df["fcf_cagr_5yr"].notna().any():
        return df

    conn = sqlite3.connect(str(DB_PATH))
    ratios = pd.read_sql(
        "SELECT company_id, year, free_cash_flow_cr FROM financial_ratios",
        conn)
    conn.close()

    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")
    ratios = ratios.sort_values(["company_id", "year"])

    fcf_cagr_map = {}
    for cid, grp in ratios.groupby("company_id"):
        vals = grp["free_cash_flow_cr"].dropna().tolist()
        if len(vals) >= 6:
            old, new = vals[-6], vals[-1]
            if old and old > 0 and new and new > 0:
                fcf_cagr_map[cid] = ((new / old) ** (1 / 5) - 1) * 100

    df["fcf_cagr_5yr"] = df["company_id"].map(fcf_cagr_map)
    return df


def impute_with_sector_median(df):
    """Impute NaN with sector median for each feature."""
    df = df.copy()
    for feat in FEATURES:
        df[feat] = pd.to_numeric(df[feat], errors="coerce")
        # Sector median
        sector_med = df.groupby("broad_sector")[feat].transform("median")
        df[feat] = df[feat].fillna(sector_med)
        # Overall median fallback
        df[feat] = df[feat].fillna(df[feat].median())
        # Final fallback: 0
        df[feat] = df[feat].fillna(0)
    return df


def cap_outliers(df):
    """Clip features to realistic ranges."""
    df = df.copy()
    for feat, (lo, hi) in CAPS.items():
        if feat in df.columns:
            df[feat] = df[feat].clip(lower=lo, upper=hi)
    return df


# ==========================================================
# Charts
# ==========================================================
def elbow_plot(scaled_data, out_path):
    """Plot inertia vs k from 2 to 10."""
    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(scaled_data)
        inertias.append(km.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), inertias, marker="o", linewidth=2, color="#1E3A5F")
    plt.axvline(x=N_CLUSTERS, color="red", linestyle="--", alpha=0.6,
                label=f"k={N_CLUSTERS} (chosen)")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"✅ Wrote {out_path}")


# ==========================================================
# Cluster naming
# ==========================================================
def name_clusters(df):
    """Assign descriptive names based on cluster profiles — no duplicates."""
    profiles = df.groupby("cluster_id")[FEATURES].median()

    names = {}
    for cid, row in profiles.iterrows():
        roe = row["return_on_equity_pct"]
        de = row["debt_to_equity"]
        rev_cagr = row["revenue_cagr_5yr"]
        opm = row["operating_profit_margin_pct"]
        fcf_cagr = row["fcf_cagr_5yr"]

        # Priority-ordered rules
        if roe > 30 and de < 1.0:
            name = "Premium Compounders"
        elif de < 0.2 and opm > 25:
            name = "High-Margin Debt-Free"
        elif de < 0.3 and opm > 15 and rev_cagr < 12:
            name = "Defensive Dividend Payers"
        elif rev_cagr > 15 and de > 1.0:
            name = "Leveraged Growth"
        elif rev_cagr > 15 and de <= 1.0:
            name = "Asset-Light Growth"
        elif roe < 8 or de > 3.0:
            name = "Distressed / Turnaround"
        else:
            name = "Value Cyclicals"

        names[cid] = name

    # Ensure unique names
    counts = Counter(names.values())
    used = {}
    final = {}
    for cid in sorted(names.keys()):
        name = names[cid]
        if counts[name] > 1:
            used[name] = used.get(name, 0) + 1
            final[cid] = f"{name} (Type {used[name]})"
        else:
            final[cid] = name

    return final


# ==========================================================
# Main
# ==========================================================
def main():
    print("=" * 60)
    print("Day 36 — KMeans Clustering")
    print("=" * 60)

    # Load + process
    df = load_features()
    print(f"Companies (valid): {len(df)}")

    df = compute_fcf_cagr_5yr(df)
    df = impute_with_sector_median(df)
    df = cap_outliers(df)

    print(f"Features: {FEATURES}")

    # Scale
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Elbow plot
    elbow_plot(X_scaled, REPORTS_DIR / "elbow_plot.png")

    # KMeans
    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    df["cluster_id"] = km.fit_predict(X_scaled)

    # Distance from assigned centroid
    distances = km.transform(X_scaled)
    df["distance_from_centroid"] = distances[np.arange(len(df)), df["cluster_id"]]

    # Cluster names
    names = name_clusters(df)
    df["cluster_name"] = df["cluster_id"].map(names)

    # Save
    output = df[[
        "company_id", "cluster_id", "cluster_name",
        "distance_from_centroid"
    ]].copy()
    output["distance_from_centroid"] = output["distance_from_centroid"].round(3)
    output.to_csv(OUTPUT_DIR / "cluster_labels.csv", index=False)
    print(f"✅ Wrote {OUTPUT_DIR / 'cluster_labels.csv'} ({len(output)} rows)")

    # Summary
    print(f"\nCluster distribution:")
    print(df["cluster_name"].value_counts().to_string())

    # Profiles
    print(f"\nCluster profiles (medians):")
    profiles = df.groupby("cluster_name")[FEATURES].median().round(1)
    print(profiles.to_string())


if __name__ == "__main__":
    main()