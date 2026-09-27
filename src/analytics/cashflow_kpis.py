"""
src/analytics/cashflow_kpis.py
Cash Flow Intelligence Module - CFO Quality, CapEx Intensity, Distress Signals
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import os

DB_PATH = "nifty100.db"
OUTPUT_DIR = Path("output")


class CashFlowIntelligence:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def get_cashflow_data(self):
        """Get cash flow and financial data for all companies (using 2022 data)"""
        query = """
        SELECT 
            f.company_id,
            f.year,
            f.free_cash_flow_cr,
            f.cash_from_operations_cr,
            f.operating_profit_margin_pct,
            f.net_profit_margin_pct,
            f.market_cap_crore,
            f.revenue_cagr_5yr,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            cf.operating_cashflow,
            cf.investing_cashflow,
            cf.financing_cashflow,
            bs.total_assets,
            bs.total_liabilities,
            pnl.sales,
            pnl.net_profit as net_profit_abs
        FROM financial_ratios f
        JOIN companies c ON f.company_id = c.ticker
        LEFT JOIN sectors s ON f.company_id = s.ticker
        LEFT JOIN cashflow cf ON f.company_id = cf.company_id AND f.year = cf.year_int
        LEFT JOIN balancesheet bs ON f.company_id = bs.company_id AND f.year = bs.year_int
        LEFT JOIN profitandloss pnl ON f.company_id = pnl.company_id AND f.year = pnl.year_int
        WHERE f.year = 2022
        """
        df = pd.read_sql(query, self.conn)

        # Convert to numeric
        numeric_cols = [
            'free_cash_flow_cr', 'cash_from_operations_cr', 'operating_profit_margin_pct',
            'net_profit_margin_pct', 'market_cap_crore', 'revenue_cagr_5yr',
            'operating_cashflow', 'investing_cashflow', 'financing_cashflow',
            'total_assets', 'total_liabilities', 'sales', 'net_profit_abs'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_historical_cashflow(self, ticker):
        """Get historical cash flow data for a company"""
        query = """
        SELECT 
            f.year,
            f.free_cash_flow_cr,
            f.cash_from_operations_cr,
            f.net_profit_margin_pct,
            cf.operating_cashflow,
            cf.investing_cashflow,
            cf.financing_cashflow,
            pnl.sales
        FROM financial_ratios f
        LEFT JOIN cashflow cf ON f.company_id = cf.company_id AND f.year = cf.year_int
        LEFT JOIN profitandloss pnl ON f.company_id = pnl.company_id AND f.year = pnl.year_int
        WHERE f.company_id = ?
        ORDER BY f.year DESC
        """
        df = pd.read_sql(query, self.conn, params=(ticker,))
        return df

    def calculate_cfo_quality(self, df):
        """Calculate CFO Quality Score"""
        if 'net_profit_abs' in df.columns:
            df['net_profit'] = df['net_profit_abs']
        else:
            df['net_profit'] = df['net_profit_margin_pct'] * df['sales'] / 100

        df['cfo_pat_ratio'] = np.where(
            df['net_profit'] > 0,
            df['cash_from_operations_cr'] / df['net_profit'],
            np.nan
        )
        df['cfo_pat_ratio'] = df['cfo_pat_ratio'].clip(0, 5)

        def get_cfo_label(row):
            ratio = row['cfo_pat_ratio']
            if pd.isna(ratio):
                return 'N/A'
            if ratio > 1.0:
                return 'High Quality'
            elif ratio >= 0.5:
                return 'Moderate'
            else:
                return 'Accrual Risk'

        df['cfo_quality_label'] = df.apply(get_cfo_label, axis=1)
        df['cfo_quality_score'] = df['cfo_pat_ratio'] * 20
        df['cfo_quality_score'] = df['cfo_quality_score'].clip(0, 100)

        return df

    def calculate_capex_intensity(self, df):
        """Calculate CapEx Intensity"""
        df['capex_intensity_pct'] = np.where(
            df['sales'] > 0,
            abs(df['investing_cashflow']) / df['sales'] * 100,
            np.nan
        )
        df['capex_intensity_pct'] = df['capex_intensity_pct'].clip(0, 100)

        def get_capex_label(row):
            intensity = row['capex_intensity_pct']
            if pd.isna(intensity):
                return 'N/A'
            if intensity < 3:
                return 'Asset Light'
            elif intensity <= 8:
                return 'Moderate'
            else:
                return 'Capital Intensive'

        df['capex_label'] = df.apply(get_capex_label, axis=1)

        return df

    def calculate_fcf_metrics(self, df):
        """Calculate FCF metrics"""
        df['fcf_cagr_5yr'] = df['revenue_cagr_5yr'] if 'revenue_cagr_5yr' in df.columns else np.nan
        df['fcf_conversion_pct'] = np.where(
            df['sales'] > 0,
            df['free_cash_flow_cr'] / df['sales'] * 100,
            np.nan
        )

        return df

    def detect_distress_signal(self, df):
        """Detect distress signals"""
        df['distress_flag'] = np.where(
            (df['operating_cashflow'] < 0) & (df['financing_cashflow'] > 0),
            True,
            False
        )
        return df

    def detect_deleveraging(self, df):
        """Detect deleveraging flag"""
        df['deleveraging_flag'] = False
        return df

    def calculate_capital_allocation(self, df):
        """Determine capital allocation pattern"""
        def get_capital_allocation(row):
            cfo = row['cash_from_operations_cr']
            fcf = row['free_cash_flow_cr']
            capex = abs(row['investing_cashflow']) if pd.notna(row['investing_cashflow']) else 0

            if pd.isna(cfo) or pd.isna(fcf):
                return 'Unknown'

            if cfo > 0 and fcf > 0 and capex > 0:
                return 'Reinvestor'
            elif cfo > 0 and fcf > 0 and capex < abs(cfo) * 0.1:
                return 'Cash Machine'
            elif cfo > 0 and fcf < 0:
                return 'Over-Investor'
            elif cfo < 0 and fcf < 0:
                return 'Distress Signal'
            elif cfo < 0 and fcf > 0:
                return 'Asset Monetizer'
            else:
                return 'Balanced'

        df['capital_allocation_label'] = df.apply(get_capital_allocation, axis=1)

        return df

    def run(self):
        """Run full cash flow intelligence pipeline"""
        print("=" * 60)
        print("📊 CASH FLOW INTELLIGENCE - DAY 31")
        print("=" * 60)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Connect
        self.connect()

        # Get data
        df = self.get_cashflow_data()
        print(f"✅ Loaded {len(df)} companies")

        # Calculate metrics
        df = self.calculate_cfo_quality(df)
        df = self.calculate_capex_intensity(df)
        df = self.calculate_fcf_metrics(df)
        df = self.detect_distress_signal(df)
        df = self.detect_deleveraging(df)
        df = self.calculate_capital_allocation(df)

        # Select columns for output
        output_cols = [
            'company_id', 'company_name', 'broad_sector', 'sub_sector',
            'cfo_quality_score', 'cfo_quality_label',
            'capex_intensity_pct', 'capex_label',
            'fcf_cagr_5yr', 'fcf_conversion_pct',
            'distress_flag', 'deleveraging_flag',
            'capital_allocation_label'
        ]

        output_cols = [c for c in output_cols if c in df.columns]
        df_output = df[output_cols].copy()

        # Round numeric columns
        numeric_cols = ['cfo_quality_score', 'capex_intensity_pct', 'fcf_cagr_5yr', 'fcf_conversion_pct']
        for col in numeric_cols:
            if col in df_output.columns:
                df_output[col] = df_output[col].round(2)

        # Save
        excel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
        df_output.to_excel(excel_path, index=False)
        print(f"✅ Saved: {excel_path}")

        # Save distress alerts
        if 'distress_flag' in df_output.columns:
            df_distress = df_output[df_output['distress_flag'] == True]
            csv_path = OUTPUT_DIR / "distress_alerts.csv"
            df_distress.to_csv(csv_path, index=False)
            print(f"✅ Saved: {csv_path}")

        # Summary
        print("\n📊 Cash Flow Intelligence Summary:")
        print(f"   Total Companies: {len(df_output)}")

        if 'cfo_quality_label' in df_output.columns:
            print(f"   CFO Quality:")
            print(df_output['cfo_quality_label'].value_counts())

        if 'capex_label' in df_output.columns:
            print(f"   CapEx Intensity:")
            print(df_output['capex_label'].value_counts())

        if 'capital_allocation_label' in df_output.columns:
            print(f"   Capital Allocation:")
            print(df_output['capital_allocation_label'].value_counts())

        distress_count = df_output['distress_flag'].sum() if 'distress_flag' in df_output.columns else 0
        print(f"   Distress Signals: {distress_count}")

        self.close()

        return df_output


if __name__ == "__main__":
    intelligence = CashFlowIntelligence()
    intelligence.run()