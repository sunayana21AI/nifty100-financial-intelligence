"""
src/nlp/pros_cons_generator.py
Auto Pros/Cons Generator - 12 pro rules and 12 con rules
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import os

DB_PATH = "nifty100.db"
OUTPUT_DIR = Path("output")


class ProsConsGenerator:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def get_company_data(self):
        """Get all company data for pros/cons generation"""
        query = """
        SELECT 
            f.company_id,
            f.year,
            f.return_on_equity_pct,
            f.return_on_capital_employed_pct,
            f.net_profit_margin_pct,
            f.debt_to_equity,
            f.free_cash_flow_cr,
            f.revenue_cagr_5yr,
            f.pat_cagr_5yr,
            f.eps_cagr_5yr,
            f.interest_coverage,
            f.asset_turnover,
            f.operating_profit_margin_pct,
            f.dividend_yield_pct,
            f.dividend_payout_ratio_pct,
            f.market_cap_crore,
            c.company_name,
            s.broad_sector,
            s.sub_sector
        FROM financial_ratios f
        JOIN companies c ON f.company_id = c.ticker
        LEFT JOIN sectors s ON f.company_id = s.ticker
        WHERE f.year = (SELECT MAX(year) FROM financial_ratios)
        """
        df = pd.read_sql(query, self.conn)

        # Convert to numeric
        numeric_cols = [
            'return_on_equity_pct', 'return_on_capital_employed_pct',
            'net_profit_margin_pct', 'debt_to_equity', 'free_cash_flow_cr',
            'revenue_cagr_5yr', 'pat_cagr_5yr', 'eps_cagr_5yr',
            'interest_coverage', 'asset_turnover', 'operating_profit_margin_pct',
            'dividend_yield_pct', 'dividend_payout_ratio_pct', 'market_cap_crore'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_historical_data(self, ticker):
        """Get historical data for a company"""
        query = """
        SELECT 
            year,
            return_on_equity_pct,
            free_cash_flow_cr,
            operating_profit_margin_pct,
            debt_to_equity,
            eps_cagr_5yr
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        """
        df = pd.read_sql(query, self.conn, params=(ticker,))
        return df

    def generate_pros(self, row, historical_df):
        """Generate pros based on 12 rules"""
        pros = []

        # Rule 1: ROE > 20% sustained for 3+ years
        if not historical_df.empty and len(historical_df) >= 3:
            roe_3yr = historical_df['return_on_equity_pct'].head(3)
            roe_clean = roe_3yr.dropna()
            if len(roe_clean) >= 3 and roe_clean.min() > 20:
                pros.append({
                    'rule_id': 1,
                    'text': 'Consistently high return on equity above 20% demonstrates exceptional capital efficiency',
                    'confidence': 90
                })

        # Rule 2: FCF positive for 5+ consecutive years
        if not historical_df.empty and len(historical_df) >= 5:
            fcf_5yr = historical_df['free_cash_flow_cr'].head(5)
            fcf_clean = fcf_5yr.dropna()
            if len(fcf_clean) >= 5 and (fcf_clean > 0).all():
                pros.append({
                    'rule_id': 2,
                    'text': 'Strong free cash flow generation over 5 years signals healthy business fundamentals',
                    'confidence': 85
                })

        # Rule 3: D/E = 0 in latest year
        if row['debt_to_equity'] == 0:
            pros.append({
                'rule_id': 3,
                'text': 'Debt-free balance sheet provides financial flexibility and eliminates interest burden',
                'confidence': 95
            })

        # Rule 4: Revenue CAGR > 15% over 5 years
        if row['revenue_cagr_5yr'] > 15:
            pros.append({
                'rule_id': 4,
                'text': f'Revenue growing at {row["revenue_cagr_5yr"]:.1f}% CAGR over 5 years reflects strong business momentum',
                'confidence': 80
            })

        # Rule 5: OPM > 25% in latest year
        if row['operating_profit_margin_pct'] > 25:
            pros.append({
                'rule_id': 5,
                'text': f'Operating profit margin above {row["operating_profit_margin_pct"]:.1f}% indicates strong pricing power and cost discipline',
                'confidence': 85
            })

        # Rule 6: PAT CAGR > 20% over 5 years
        if row['pat_cagr_5yr'] > 20:
            pros.append({
                'rule_id': 6,
                'text': f'Net profit compounding at {row["pat_cagr_5yr"]:.1f}% over 5 years creates significant shareholder value',
                'confidence': 80
            })

        # Rule 7: ICR > 10 or Debt Free
        if row['interest_coverage'] > 10 or row['debt_to_equity'] == 0:
            pros.append({
                'rule_id': 7,
                'text': 'Very high interest coverage ratio reflects negligible financial stress from debt servicing',
                'confidence': 85
            })

        # Rule 8: Dividend Yield > 2% with FCF positive
        if row['dividend_yield_pct'] > 2 and row['free_cash_flow_cr'] > 0:
            pros.append({
                'rule_id': 8,
                'text': f'Consistent dividend yield above {row["dividend_yield_pct"]:.1f}% backed by positive free cash flow',
                'confidence': 75
            })

        # Rule 9: EPS CAGR > 15% over 5 years
        if row['eps_cagr_5yr'] > 15:
            pros.append({
                'rule_id': 9,
                'text': f'Earnings per share growing at {row["eps_cagr_5yr"]:.1f}% CAGR indicates strong earnings quality and compounding',
                'confidence': 80
            })

        # Rule 10: ROE improving for 3 consecutive years
        if not historical_df.empty and len(historical_df) >= 3:
            roe_3yr = historical_df['return_on_equity_pct'].head(3)
            roe_clean = roe_3yr.dropna()
            if len(roe_clean) >= 3 and (roe_clean.diff().dropna() > 0).all():
                pros.append({
                    'rule_id': 10,
                    'text': 'Return on equity improving for 3 consecutive years shows strengthening business quality',
                    'confidence': 85
                })

        # Rule 11: Revenue CAGR < PAT CAGR (operating leverage)
        if row['revenue_cagr_5yr'] < row['pat_cagr_5yr']:
            pros.append({
                'rule_id': 11,
                'text': 'Revenue growing slower than profits shows improving operating leverage and scale benefits',
                'confidence': 70
            })

        # Rule 12: Growing asset base with declining debt
        if row['market_cap_crore'] > 50000 and row['debt_to_equity'] < 0.5:
            pros.append({
                'rule_id': 12,
                'text': 'Growing asset base funded by internal accruals reflects self-sustaining growth',
                'confidence': 70
            })

        return pros

    def generate_cons(self, row, historical_df):
        """Generate cons based on 12 rules"""
        cons = []
        sector = row['broad_sector']
        de = row['debt_to_equity']

        # Rule 1: D/E > 2.0 for non-financial companies
        if sector and 'Financials' not in sector and de > 2.0:
            cons.append({
                'rule_id': 1,
                'text': f'Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring',
                'confidence': 85
            })

        # Rule 2: FCF negative for 3 consecutive years
        if not historical_df.empty and len(historical_df) >= 3:
            fcf_3yr = historical_df['free_cash_flow_cr'].head(3)
            fcf_clean = fcf_3yr.dropna()
            if len(fcf_clean) >= 3 and (fcf_clean < 0).all():
                cons.append({
                    'rule_id': 2,
                    'text': 'Free cash flow negative for 3 consecutive years raises concern about cash generation quality',
                    'confidence': 90
                })

        # Rule 3: OPM declining for 3 consecutive years
        if not historical_df.empty and len(historical_df) >= 3:
            opm_3yr = historical_df['operating_profit_margin_pct'].head(3)
            opm_clean = opm_3yr.dropna()
            if len(opm_clean) >= 3 and (opm_clean.diff().dropna() < 0).all():
                cons.append({
                    'rule_id': 3,
                    'text': 'Operating margins declining for 3 consecutive years suggests pricing or cost pressure',
                    'confidence': 80
                })

        # Rule 4: Net profit negative in latest year
        if row['net_profit_margin_pct'] < 0:
            cons.append({
                'rule_id': 4,
                'text': 'Company reported a net loss in the most recent financial year',
                'confidence': 95
            })

        # Rule 5: Revenue declining for 2+ years
        if row['revenue_cagr_5yr'] < 0:
            cons.append({
                'rule_id': 5,
                'text': 'Revenue contraction over recent years indicates demand weakness or market share loss',
                'confidence': 80
            })

        # Rule 6: ICR < 1.5
        if row['interest_coverage'] < 1.5 and row['interest_coverage'] > 0:
            cons.append({
                'rule_id': 6,
                'text': f'Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations',
                'confidence': 90
            })

        # Rule 7: Dividend payout > 100%
        if row['dividend_payout_ratio_pct'] > 100:
            cons.append({
                'rule_id': 7,
                'text': f'Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable',
                'confidence': 85
            })

        # Rule 8: D/E rising for 3 consecutive years
        if not historical_df.empty and len(historical_df) >= 3:
            de_3yr = historical_df['debt_to_equity'].head(3)
            de_clean = de_3yr.dropna()
            if len(de_clean) >= 3 and (de_clean.diff().dropna() > 0).all():
                cons.append({
                    'rule_id': 8,
                    'text': 'Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk',
                    'confidence': 80
                })

        # Rule 9: EPS declining for 3 consecutive years
        if not historical_df.empty and len(historical_df) >= 3:
            eps_3yr = historical_df['eps_cagr_5yr'].head(3)
            eps_clean = eps_3yr.dropna()
            if len(eps_clean) >= 3 and (eps_clean.diff().dropna() < 0).all():
                cons.append({
                    'rule_id': 9,
                    'text': 'Earnings per share declining for 3 consecutive years reflects deteriorating profitability',
                    'confidence': 85
                })

        # Rule 10: ROCE < 10%
        if row['return_on_capital_employed_pct'] < 10:
            cons.append({
                'rule_id': 10,
                'text': f'Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital',
                'confidence': 75
            })

        # Rule 11: Revenue CAGR < 5% over 5 years
        if row['revenue_cagr_5yr'] < 5:
            cons.append({
                'rule_id': 11,
                'text': f'Revenue growing at below {row["revenue_cagr_5yr"]:.1f}% over 5 years lags inflation and suggests limited business momentum',
                'confidence': 70
            })

        # Rule 12: Net Debt > 3x EBITDA
        if de > 3:
            cons.append({
                'rule_id': 12,
                'text': f'Debt-to-equity ratio of {de:.2f} indicates high leverage and limits financial flexibility',
                'confidence': 80
            })

        return cons

    def generate_pros_cons(self, df):
        """Generate pros and cons for all companies"""
        all_pros = []
        all_cons = []
        skipped = []

        for idx, row in df.iterrows():
            ticker = row['company_id']

            # Get historical data
            historical_df = self.get_historical_data(ticker)

            # Generate pros
            pros = self.generate_pros(row, historical_df)
            for p in pros:
                if p['confidence'] >= 60:
                    all_pros.append({
                        'company_id': ticker,
                        'type': 'pro',
                        'rule_id': p['rule_id'],
                        'text': p['text'],
                        'confidence_pct': p['confidence']
                    })

            # Generate cons
            cons = self.generate_cons(row, historical_df)
            for c in cons:
                if c['confidence'] >= 60:
                    all_cons.append({
                        'company_id': ticker,
                        'type': 'con',
                        'rule_id': c['rule_id'],
                        'text': c['text'],
                        'confidence_pct': c['confidence']
                    })

            # Check if company has at least 1 pro and 1 con
            if not any(p['company_id'] == ticker for p in all_pros) or \
               not any(c['company_id'] == ticker for c in all_cons):
                skipped.append(ticker)

        # Combine pros and cons
        df_pros = pd.DataFrame(all_pros)
        df_cons = pd.DataFrame(all_cons)
        df_all = pd.concat([df_pros, df_cons], ignore_index=True)

        print(f"\n📊 Pros/Cons Summary:")
        print(f"   Total pros: {len(all_pros)}")
        print(f"   Total cons: {len(all_cons)}")
        print(f"   Total: {len(df_all)}")
        print(f"   Companies with < 1 pro or con: {len(skipped)}")

        return df_all, skipped

    def run(self):
        """Run full pros/cons generation"""
        print("=" * 60)
        print("📊 AUTO PROS/CONS GENERATOR - DAY 30")
        print("=" * 60)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Connect to database first
        self.connect()

        # Get data
        df = self.get_company_data()
        print(f"✅ Loaded {len(df)} companies")

        # Generate pros and cons
        df_pros_cons, skipped = self.generate_pros_cons(df)

        # Save
        output_path = OUTPUT_DIR / "pros_cons_generated.csv"
        df_pros_cons.to_csv(output_path, index=False)
        print(f"✅ Saved: {output_path}")

        # Save skipped companies
        if skipped:
            df_skipped = pd.DataFrame({'company_id': skipped})
            skipped_path = OUTPUT_DIR / "skipped_pros_cons.csv"
            df_skipped.to_csv(skipped_path, index=False)
            print(f"✅ Saved skipped companies: {skipped_path}")

        self.close()

        print("\n✅ Pros/Cons generation complete!")
        return df_pros_cons


if __name__ == "__main__":
    generator = ProsConsGenerator()
    generator.run()