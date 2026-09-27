import sqlite3
import pandas as pd
from pathlib import Path

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    asset_turnover,
    return_on_equity,
    debt_to_equity
)

from src.analytics.cashflow_kpis import free_cash_flow

from src.analytics.cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr
)


DB_PATH = "nifty100.db"
RAW_DIR = Path("data/raw")

FINANCIAL_RATIOS_FILE = RAW_DIR / "financial_ratios.xlsx"
MARKET_CAP_FILE = RAW_DIR / "market_cap.xlsx"


def normalize_year(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.upper() in ["TTM", "NA", "N/A", ""]:
        return None

    import re

    match = re.search(r"\d{4}", value)
    if match:
        return int(match.group())

    match = re.search(r"\d{2}$", value)
    if match:
        return 2000 + int(match.group())

    return None


def calculate_company_cagr(pnl):
    lookup = {}

    pnl = pnl.copy()
    pnl["year_clean"] = pnl["year"].apply(normalize_year)

    for company, group in pnl.groupby("company_id"):

        group = (
            group
            .dropna(subset=["year_clean"])
            .sort_values("year_clean")
            .drop_duplicates(subset=["year_clean"], keep="first")
        )

        if len(group) < 6:
            continue

        start = group.iloc[-6]
        end = group.iloc[-1]

        revenue, _ = revenue_cagr(
            start["sales"],
            end["sales"],
            5
        )

        pat, _ = pat_cagr(
            start["net_profit"],
            end["net_profit"],
            5
        )

        lookup[company] = {
            "revenue_cagr_5yr": revenue,
            "pat_cagr_5yr": pat
        }

    return lookup


def calculate_eps_cagr(raw_ratios):
    lookup = {}

    df = raw_ratios.copy()

    df = (
        df
        .dropna(subset=["year_clean"])
        .sort_values(["company_id", "year_clean"])
        .drop_duplicates(
            subset=["company_id", "year_clean"],
            keep="first"
        )
    )

    for company, group in df.groupby("company_id"):

        group = group.dropna(
            subset=["earnings_per_share"]
        )

        if len(group) < 6:
            continue

        start = group.iloc[-6]
        end = group.iloc[-1]

        eps_value, _ = eps_cagr(
            start["earnings_per_share"],
            end["earnings_per_share"],
            5
        )

        lookup[company] = eps_value

    return lookup


def load_raw_financial_ratios():
    print("Loading raw financial ratios...")

    raw = pd.read_excel(
        FINANCIAL_RATIOS_FILE,
        sheet_name="Sheet1"
    )

    raw["company_id"] = (
        raw["company_id"]
        .astype(str)
        .str.strip()
    )

    raw["year_clean"] = (
        raw["year"]
        .apply(normalize_year)
    )

    # All numeric columns from the Excel file
    numeric_columns = [
        "interest_coverage",
        "earnings_per_share",
        "dividend_payout_ratio_pct",
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "debt_to_equity",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "book_value_per_share",
        "total_debt_cr",
        "cash_from_operations_cr"
    ]

    for column in numeric_columns:
        if column in raw.columns:
            raw[column] = pd.to_numeric(
                raw[column],
                errors="coerce"
            )

    raw = (
        raw
        .dropna(subset=["year_clean"])
        .sort_values(["company_id", "year_clean", "id"])
        .drop_duplicates(
            subset=["company_id", "year_clean"],
            keep="first"
        )
    )

    eps_cagr_lookup = calculate_eps_cagr(raw)

    # Select all columns including ROE and other ratios
    selected = raw[
        [
            "company_id",
            "year_clean",
            "interest_coverage",
            "earnings_per_share",
            "dividend_payout_ratio_pct",
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "debt_to_equity",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "book_value_per_share",
            "total_debt_cr",
            "cash_from_operations_cr"
        ]
    ].copy()

    selected["eps_cagr_5yr"] = (
        selected["company_id"]
        .map(eps_cagr_lookup)
    )

    return selected


def load_market_cap():
    print("Loading market cap data...")

    market = pd.read_excel(
        MARKET_CAP_FILE,
        sheet_name="Sheet1"
    )

    market["company_id"] = (
        market["company_id"]
        .astype(str)
        .str.strip()
    )

    market["year_clean"] = (
        market["year"]
        .apply(normalize_year)
    )

    numeric_columns = [
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct"
    ]

    for column in numeric_columns:
        market[column] = pd.to_numeric(
            market[column],
            errors="coerce"
        )

    market = (
        market
        .dropna(subset=["year_clean"])
        .sort_values(["company_id", "year_clean", "id"])
        .drop_duplicates(
            subset=["company_id", "year_clean"],
            keep="first"
        )
    )

    return market[
        [
            "company_id",
            "year_clean",
            "market_cap_crore",
            "pe_ratio",
            "pb_ratio",
            "dividend_yield_pct"
        ]
    ]


def load_ratios():
    
    conn = sqlite3.connect(DB_PATH)

    print("Loading tables...")

    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    companies = pd.read_sql("SELECT company_id, ticker FROM companies", conn)

    # Clean P&L
    pnl["company_id"] = (
        pnl["company_id_y"]
        if "company_id_y" in pnl.columns
        else pnl["company_id"]
    )
    pnl = pnl.drop(columns=[c for c in ["company_id_x", "company_id_y", "ticker"] if c in pnl.columns])

    # Clean Cash Flow
    cf["company_id"] = cf["company_id"].astype(float).astype("Int64")
    cf = cf.merge(companies, on="company_id", how="left")
    cf["company_id"] = cf["ticker"]
    cf.drop(columns=["ticker"], inplace=True)

    # Normalize years
    pnl["year_clean"] = pnl["year"].apply(normalize_year)
    bs["year_clean"] = bs["year"].apply(normalize_year)
    cf["year_clean"] = cf["year"].apply(normalize_year)

    # Merge core financial data
    df = pnl.merge(bs, on=["company_id", "year_clean"], how="left")
    df = df.merge(cf, on=["company_id", "year_clean"], how="left")
    df = df[df["company_id"].notna()]
    df = df[df["year_clean"].notna()]
    df = df.drop_duplicates(subset=["company_id", "year_clean"])
    print("Merged rows:", len(df))

    # CAGR
    cagr_lookup = calculate_company_cagr(pnl)

    # ✅ RAW FINANCIAL RATIOS (AB ISME ROE BHI HAI)
    raw_ratios = load_raw_financial_ratios()
    df = df.merge(raw_ratios, on=["company_id", "year_clean"], how="left")

    # Market Cap
    market_cap = load_market_cap()
    df = df.merge(market_cap, on=["company_id", "year_clean"], how="left")

    records = []

    for _, row in df.iterrows():

        sales = row.get("sales")
        profit = row.get("net_profit")
        op_profit = row.get("operating_profit")
        assets = row.get("total_assets")
        liabilities = row.get("total_liabilities")

        npm = net_profit_margin(profit, sales)
        opm = operating_profit_margin(op_profit, sales)
        if isinstance(opm, tuple):
            opm = opm[0]
        roa = return_on_assets(profit, assets)

        # 🔴 CHANGE YAHAN: Excel ROE use karo
        roe = row.get("return_on_equity_pct")  # Pehle Excel ROE
        if pd.isna(roe):  # Agar NULL hai toh calculated use karo
            roe = return_on_equity(profit, assets, liabilities)
        
        de = debt_to_equity(liabilities, assets)
        turnover = asset_turnover(sales, assets)

        cfo = row.get("operating_cashflow")
        cfi = row.get("investing_cashflow")
        fcf = free_cash_flow(cfo, cfi)

        company_cagr = cagr_lookup.get(row["company_id"], {})

        records.append({
            "company_id": row["company_id"],
            "year": row["year_clean"],
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_assets_pct": roa,
            "return_on_equity_pct": roe,  # ✅ Excel ROE
            "debt_to_equity": de,
            "asset_turnover": turnover,
            "free_cash_flow_cr": fcf,
            "cash_from_operations_cr": cfo,
            "revenue_cagr_5yr": company_cagr.get("revenue_cagr_5yr"),
            "pat_cagr_5yr": company_cagr.get("pat_cagr_5yr"),
            "interest_coverage": row.get("interest_coverage"),
            "earnings_per_share": row.get("earnings_per_share"),
            "dividend_payout_ratio_pct": row.get("dividend_payout_ratio_pct"),
            "eps_cagr_5yr": row.get("eps_cagr_5yr"),
            "market_cap_crore": row.get("market_cap_crore"),
            "pe_ratio": row.get("pe_ratio"),
            "pb_ratio": row.get("pb_ratio"),
            "dividend_yield_pct": row.get("dividend_yield_pct")
        })

    result = pd.DataFrame(records)

    print("\nFinal ratio columns:")
    print(result.columns.tolist())
    print("\nFinal rows:", len(result))
    
    # result DataFrame banane ke BAAD, to_sql() se PEHLE
    # result DataFrame banane ke BAAD, to_sql() se PEHLE
    print("\n===== DEBUG: result DataFrame =====")
    print(f"Total rows: {len(result)}")
    print(f"ROE non-null count: {result['return_on_equity_pct'].count()}")
    print(f"ROE sample values:\n{result[['company_id', 'year', 'return_on_equity_pct']].head(10)}")
    print("===================================\n")

    # Replace old ratio table
    conn.execute("DELETE FROM financial_ratios")
    conn.commit()
    
    
    result.to_sql("financial_ratios", conn, if_exists="append", index=False)
    print(f"\nInserted {len(result)} rows")
    conn.close()


if __name__ == "__main__":
    load_ratios()