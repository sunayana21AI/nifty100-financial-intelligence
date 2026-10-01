"""
src/nlp/pros_cons_generator.py
Auto-generate pros and cons for all companies.

12 primary pro rules + 12 primary con rules + universal fallbacks
so that every company gets at least 1 pro and 1 con.
"""
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CONFIDENCE_THRESHOLD = 60


# ==========================================================
# Helpers
# ==========================================================
def _num(x):
    if x is None or pd.isna(x):
        return 0.0
    try:
        return float(x)
    except Exception:
        return 0.0


def _consecutive_increase(vals):
    if len(vals) < 3:
        return False
    return vals[-1] > vals[-2] > vals[-3]


def _consecutive_decrease(vals):
    if len(vals) < 3:
        return False
    return vals[-1] < vals[-2] < vals[-3]


# ==========================================================
# Build per-company history
# ==========================================================
def build_company_history():
    conn = sqlite3.connect(str(DB_PATH))

    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    sectors = pd.read_sql("SELECT ticker, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT ticker, company_name FROM companies", conn)
    conn.close()

    sectors = sectors.rename(columns={"ticker": "company_id"})
    companies = companies.rename(columns={"ticker": "company_id"})
    ratios = ratios.merge(sectors, on="company_id", how="left")
    ratios = ratios.merge(companies, on="company_id", how="left")

    for df in (ratios, cf, pl, bs):
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")

    history = {}

    for cid in ratios["company_id"].dropna().unique():
        r = ratios[ratios["company_id"] == cid].sort_values("year")
        c = cf[cf["company_id"] == cid].sort_values("year")
        p = pl[pl["company_id"] == cid].sort_values("year")
        b = bs[bs["company_id"] == cid].sort_values("year")

        if r.empty:
            continue

        latest = r.iloc[-1]

        roe_vals = [_num(x) for x in r["return_on_equity_pct"].dropna().tolist()]
        roe_3yr = roe_vals[-3:] if len(roe_vals) >= 3 else roe_vals
        roe_3yr_avg = float(np.mean(roe_3yr)) if roe_3yr else 0.0
        roe_3yr_increasing = _consecutive_increase(roe_vals)

        opm_vals = [_num(x) for x in r["operating_profit_margin_pct"].dropna().tolist()]
        opm_3yr_declining = _consecutive_decrease(opm_vals)

        cfo_vals = []
        if "operating_cashflow" in c.columns:
            cfo_vals = [_num(x) for x in c["operating_cashflow"].dropna().tolist()]
        fcf_pos_years_5 = sum(1 for v in cfo_vals[-5:] if v > 0)
        fcf_neg_years_3 = (len(cfo_vals) >= 3 and all(v < 0 for v in cfo_vals[-3:]))

        rev_vals = []
        if "sales" in p.columns:
            rev_vals = [_num(x) for x in p["sales"].dropna().tolist()]
        rev_declining_2 = (len(rev_vals) >= 3 and
                           rev_vals[-1] < rev_vals[-2] < rev_vals[-3])

        pat_vals = []
        if "net_profit" in p.columns:
            pat_vals = [_num(x) for x in p["net_profit"].dropna().tolist()]
        latest_pat = pat_vals[-1] if pat_vals else 0.0

        eps_vals = [_num(x) for x in r["earnings_per_share"].dropna().tolist()]
        eps_3yr_declining = _consecutive_decrease(eps_vals)

        de_vals = [_num(x) for x in r["debt_to_equity"].dropna().tolist()]
        de_3yr_increasing = _consecutive_increase(de_vals)
        de_3yr_decreasing = _consecutive_decrease(de_vals)

        assets_vals = []
        if "total_assets" in b.columns:
            assets_vals = [_num(x) for x in b["total_assets"].dropna().tolist()]
        assets_3yr_increasing = _consecutive_increase(assets_vals)

        history[cid] = {
            "company_name":          str(latest.get("company_name", cid) or cid),
            "sector":                str(latest.get("broad_sector", "") or ""),
            "roe_3yr_avg":           roe_3yr_avg,
            "roe_3yr_increasing":    roe_3yr_increasing,
            "latest_opm":            _num(latest.get("operating_profit_margin_pct")),
            "opm_3yr_declining":     opm_3yr_declining,
            "rev_cagr_5yr":          _num(latest.get("revenue_cagr_5yr")),
            "pat_cagr_5yr":          _num(latest.get("pat_cagr_5yr")),
            "eps_cagr_5yr":          _num(latest.get("eps_cagr_5yr")),
            "latest_de":             _num(latest.get("debt_to_equity")),
            "latest_icr":            _num(latest.get("interest_coverage")),
            "latest_roce":           _num(latest.get("return_on_capital_employed_pct")),
            "latest_div_yield":      _num(latest.get("dividend_yield_pct")),
            "latest_payout":         _num(latest.get("dividend_payout_ratio_pct")),
            "latest_fcf":            _num(latest.get("free_cash_flow_cr")),
            "latest_net_profit":     latest_pat,
            "latest_pe":             _num(latest.get("pe_ratio")),
            "fcf_positive_years_5":  fcf_pos_years_5,
            "fcf_negative_years_3":  fcf_neg_years_3,
            "rev_declining_years_2": rev_declining_2,
            "eps_3yr_declining":     eps_3yr_declining,
            "de_3yr_increasing":     de_3yr_increasing,
            "de_3yr_decreasing":     de_3yr_decreasing,
            "assets_3yr_increasing": assets_3yr_increasing,
            "num_years_data":        len(r),
        }

    # Attach sector median PE
    sector_pes = {}
    for cid, h in history.items():
        pe = h["latest_pe"]
        if pe > 0:
            sector_pes.setdefault(h["sector"], []).append(pe)

    sector_median_map = {
        sec: float(np.median(pes)) for sec, pes in sector_pes.items() if pes
    }
    for cid, h in history.items():
        h["sector_median_pe"] = sector_median_map.get(h["sector"], 0.0)

    return history


# ==========================================================
# PRIMARY PRO RULES
# ==========================================================
PRO_RULES = [
    ("P1", lambda h: h["roe_3yr_avg"] > 20,
     lambda h: f"Consistently high return on equity above 20% "
               f"({h['roe_3yr_avg']:.1f}%) demonstrates exceptional capital efficiency",
     lambda h: min(100.0, h["roe_3yr_avg"] * 3)),

    ("P2", lambda h: h["fcf_positive_years_5"] >= 5,
     lambda h: "Strong free cash flow generation over 5 years signals "
               "healthy business fundamentals",
     lambda h: 90.0),

    ("P3", lambda h: h["latest_de"] <= 0.05,
     lambda h: "Debt-free balance sheet provides financial flexibility and "
               "eliminates interest burden",
     lambda h: 95.0),

    ("P4", lambda h: h["rev_cagr_5yr"] > 15,
     lambda h: f"Revenue growing at above 15% CAGR over 5 years "
               f"({h['rev_cagr_5yr']:.1f}%) reflects strong business momentum",
     lambda h: min(100.0, h["rev_cagr_5yr"] * 4)),

    ("P5", lambda h: h["latest_opm"] > 25,
     lambda h: f"Operating profit margin above 25% ({h['latest_opm']:.1f}%) "
               f"indicates strong pricing power and cost discipline",
     lambda h: min(100.0, h["latest_opm"] * 3)),

    ("P6", lambda h: h["pat_cagr_5yr"] > 20,
     lambda h: f"Net profit compounding at above 20% over 5 years "
               f"({h['pat_cagr_5yr']:.1f}%) creates significant shareholder value",
     lambda h: min(100.0, h["pat_cagr_5yr"] * 3)),

    ("P7", lambda h: h["latest_icr"] > 10 or h["latest_de"] <= 0.05,
     lambda h: "Very high interest coverage ratio reflects negligible "
               "financial stress from debt servicing",
     lambda h: 85.0),

    ("P8", lambda h: h["latest_div_yield"] > 2 and h["latest_fcf"] > 0,
     lambda h: f"Consistent dividend yield above 2% ({h['latest_div_yield']:.1f}%) "
               f"backed by positive free cash flow",
     lambda h: 80.0),

    ("P9", lambda h: h["eps_cagr_5yr"] > 15,
     lambda h: f"Earnings per share growing above 15% CAGR "
               f"({h['eps_cagr_5yr']:.1f}%) indicates strong earnings quality",
     lambda h: min(100.0, h["eps_cagr_5yr"] * 4)),

    ("P10", lambda h: h["roe_3yr_increasing"],
     lambda h: "Return on equity improving for 3 consecutive years shows "
               "strengthening business quality",
     lambda h: 75.0),

    ("P11", lambda h: 0 < h["rev_cagr_5yr"] < h["pat_cagr_5yr"],
     lambda h: "Revenue growing slower than profits shows improving "
               "operating leverage and scale benefits",
     lambda h: 70.0),

    ("P12", lambda h: h["assets_3yr_increasing"] and h["de_3yr_decreasing"],
     lambda h: "Growing asset base funded by internal accruals reflects "
               "self-sustaining growth",
     lambda h: 70.0),
]


# ==========================================================
# PRIMARY CON RULES
# ==========================================================
CON_RULES = [
    ("C1", lambda h: h["latest_de"] > 2.0 and "Financial" not in h["sector"],
     lambda h: f"Debt-to-equity ratio of {h['latest_de']:.2f} is elevated "
               f"for a non-financial company and warrants monitoring",
     lambda h: min(100.0, h["latest_de"] * 25)),

    ("C2", lambda h: h["fcf_negative_years_3"],
     lambda h: "Free cash flow negative for 3 consecutive years raises "
               "concern about cash generation quality",
     lambda h: 85.0),

    ("C3", lambda h: h["opm_3yr_declining"],
     lambda h: "Operating margins declining for 3 consecutive years suggest "
               "pricing or cost pressure",
     lambda h: 80.0),

    ("C4", lambda h: h["latest_net_profit"] < 0,
     lambda h: "Company reported a net loss in the most recent financial year",
     lambda h: 95.0),

    ("C5", lambda h: h["rev_declining_years_2"],
     lambda h: "Revenue contraction over 2 consecutive years indicates "
               "demand weakness or market share loss",
     lambda h: 85.0),

    ("C6", lambda h: 0 < h["latest_icr"] < 1.5,
     lambda h: f"Interest coverage ratio below 1.5x ({h['latest_icr']:.2f}) "
               f"indicates the company is at risk of not meeting its debt obligations",
     lambda h: 90.0),

    ("C7", lambda h: h["latest_payout"] > 100,
     lambda h: f"Dividend payout ratio above 100% ({h['latest_payout']:.1f}%) "
               f"means the company is paying dividends from reserves, "
               f"which is unsustainable",
     lambda h: 80.0),

    ("C8", lambda h: h["de_3yr_increasing"],
     lambda h: "Rising debt-to-equity ratio over 3 years suggests increasing "
               "financial leverage risk",
     lambda h: 75.0),

    ("C9", lambda h: h["eps_3yr_declining"],
     lambda h: "Earnings per share declining for 3 consecutive years "
               "reflects deteriorating profitability",
     lambda h: 80.0),

    ("C10", lambda h: 0 < h["latest_roce"] < 10,
     lambda h: f"Return on capital employed below 10% ({h['latest_roce']:.1f}%) "
               f"suggests the business is not generating sufficient returns "
               f"on invested capital",
     lambda h: 70.0),

    ("C11", lambda h: h["latest_de"] > 3.0,
     lambda h: f"Debt-to-equity above 3x ({h['latest_de']:.2f}) is a high "
               f"leverage ratio and limits financial flexibility",
     lambda h: 85.0),

    ("C12", lambda h: h["rev_cagr_5yr"] < 5,
     lambda h: f"Revenue growing at below 5% over 5 years "
               f"({h['rev_cagr_5yr']:.1f}%) lags inflation and suggests "
               f"limited business momentum",
     lambda h: 70.0),
]


# ==========================================================
# UNIVERSAL FALLBACK RULES (guaranteed to match)
# ==========================================================
FALLBACK_PRO = {
    "rule_id": "P99",
    "text_fn": lambda h: f"Established player in {h['sector'] or 'its sector'} "
                         f"with {h['num_years_data']} years of financial data, "
                         f"demonstrating business continuity and scale",
    "confidence": 65.0,
}

FALLBACK_CON = {
    "rule_id": "C99",
    "text_fn": lambda h: f"Investors should monitor competitive dynamics and "
                         f"execution risks typical of the "
                         f"{h['sector'] or 'broader'} sector",
    "confidence": 65.0,
}


# ==========================================================
# Main generation
# ==========================================================
def generate_pros_cons() -> pd.DataFrame:
    print(f"[pros_cons] Reading from: {DB_PATH}")
    history = build_company_history()
    print(f"[pros_cons] Companies loaded: {len(history)}")

    results = []

    # ---- Pass 1: primary rules ----
    for cid, h in history.items():
        for rule_id, cond_fn, text_fn, conf_fn in PRO_RULES:
            try:
                if cond_fn(h):
                    conf = float(conf_fn(h))
                    if conf > CONFIDENCE_THRESHOLD:
                        results.append({
                            "company_id": cid, "type": "pro", "rule_id": rule_id,
                            "text": text_fn(h), "confidence_pct": round(conf, 1),
                        })
            except Exception:
                pass

        for rule_id, cond_fn, text_fn, conf_fn in CON_RULES:
            try:
                if cond_fn(h):
                    conf = float(conf_fn(h))
                    if conf > CONFIDENCE_THRESHOLD:
                        results.append({
                            "company_id": cid, "type": "con", "rule_id": rule_id,
                            "text": text_fn(h), "confidence_pct": round(conf, 1),
                        })
            except Exception:
                pass

    # ---- Pass 2: universal fallback for anyone still missing ----
    df_partial = pd.DataFrame(results)

    for cid, h in history.items():
        cid_df = df_partial[df_partial["company_id"] == cid] if not df_partial.empty else pd.DataFrame()
        has_pro = (cid_df["type"] == "pro").any() if not cid_df.empty else False
        has_con = (cid_df["type"] == "con").any() if not cid_df.empty else False

        if not has_pro:
            results.append({
                "company_id": cid, "type": "pro",
                "rule_id": FALLBACK_PRO["rule_id"],
                "text": FALLBACK_PRO["text_fn"](h),
                "confidence_pct": FALLBACK_PRO["confidence"],
            })

        if not has_con:
            results.append({
                "company_id": cid, "type": "con",
                "rule_id": FALLBACK_CON["rule_id"],
                "text": FALLBACK_CON["text_fn"](h),
                "confidence_pct": FALLBACK_CON["confidence"],
            })

    df = pd.DataFrame(
        results,
        columns=["company_id", "type", "rule_id", "text", "confidence_pct"],
    )
    df.to_csv(OUTPUT_DIR / "pros_cons_generated.csv", index=False)

    print(f"\n✅ Generated {len(df)} pros/cons entries")
    print(f"   Companies covered: {df['company_id'].nunique()}")
    print(f"   Pros: {(df['type'] == 'pro').sum()}")
    print(f"   Cons: {(df['type'] == 'con').sum()}")

    # ---- Verify ----
    print(f"\n[verify] Coverage check:")
    missing_pro, missing_con = [], []
    for cid in history:
        cid_df = df[df["company_id"] == cid]
        if not (cid_df["type"] == "pro").any():
            missing_pro.append(cid)
        if not (cid_df["type"] == "con").any():
            missing_con.append(cid)

    print(f"   Companies missing PRO: {len(missing_pro)}")
    print(f"   Companies missing CON: {len(missing_con)}")

    if not missing_pro and not missing_con:
        print(f"   ✅ 100% coverage — every company has ≥1 pro and ≥1 con")

    return df


if __name__ == "__main__":
    generate_pros_cons()