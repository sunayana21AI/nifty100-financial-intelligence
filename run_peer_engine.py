"""
Peer Engine - Day 18
Run this file directly: python run_peer_engine.py
"""

import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path

DB_PATH = "nifty100.db"
RAW_DIR = Path("data/raw")
PEER_FILE = RAW_DIR / "peer_groups.xlsx"

class PeerEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.peer_groups = None
        self.metrics = [
            'return_on_equity_pct',
            'return_on_capital_employed_pct',
            'net_profit_margin_pct',
            'debt_to_equity',
            'free_cash_flow_cr',
            'pat_cagr_5yr',
            'revenue_cagr_5yr',
            'eps_cagr_5yr',
            'interest_coverage',
            'asset_turnover'
        ]

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def load_peer_groups(self):
        if not PEER_FILE.exists():
            raise FileNotFoundError(f"Peer groups file not found: {PEER_FILE}")
        df = pd.read_excel(PEER_FILE)
        print(f"✅ Loaded peer groups: {len(df)} rows")
        print(f"   Columns: {df.columns.tolist()}")
        peer_col = 'peer_group_name'
        print(f"   Using peer group column: {peer_col}")
        print(f"   Unique peer groups: {df[peer_col].nunique()}")
        print(f"   Peer groups: {df[peer_col].unique().tolist()}")
        self.peer_groups = df
        return df

    def get_latest_financial_data(self):
        query = """
        SELECT 
            f.company_id,
            f.year,
            f.return_on_equity_pct,
            f.return_on_capital_employed_pct,
            f.net_profit_margin_pct,
            f.debt_to_equity,
            f.free_cash_flow_cr,
            f.pat_cagr_5yr,
            f.revenue_cagr_5yr,
            f.eps_cagr_5yr,
            f.interest_coverage,
            f.asset_turnover,
            c.company_name,
            c.ticker
        FROM financial_ratios f
        JOIN companies c ON f.company_id = c.ticker
        WHERE f.year = (SELECT MAX(year) FROM financial_ratios)
        """
        df = pd.read_sql(query, self.conn)
        print(f"✅ Loaded financial data: {len(df)} companies")
        return df

    def calculate_percentiles(self, df_financial):
        df_merged = df_financial.merge(
            self.peer_groups[['company_id', 'peer_group_name']],
            on='company_id',
            how='left'
        )
        print(f"\n📊 Merged data: {len(df_merged)} rows")
        missing_peers = df_merged[df_merged['peer_group_name'].isna()]['company_id'].tolist()
        if missing_peers:
            print(f"⚠️ Companies without peer groups: {len(missing_peers)}")
            print(f"   {missing_peers[:10]}")
        percentile_results = []
        for metric in self.metrics:
            if metric not in df_merged.columns:
                print(f"⚠️ Metric not found: {metric}")
                continue
            print(f"   Calculating percentiles for: {metric}")
            for peer_group in df_merged['peer_group_name'].dropna().unique():
                mask = df_merged['peer_group_name'] == peer_group
                group_data = df_merged.loc[mask].copy()
                group_data = group_data[group_data[metric].notna()]
                if len(group_data) < 2:
                    continue
                if metric == 'debt_to_equity':
                    group_data['percentile_rank'] = 1 - group_data[metric].rank(pct=True)
                else:
                    group_data['percentile_rank'] = group_data[metric].rank(pct=True)
                for _, row in group_data.iterrows():
                    percentile_results.append({
                        'company_id': row['company_id'],
                        'peer_group_name': peer_group,
                        'metric': metric,
                        'value': row[metric],
                        'percentile_rank': row['percentile_rank'],
                        'year': row['year']
                    })
        df_percentiles = pd.DataFrame(percentile_results)
        print(f"\n✅ Calculated {len(df_percentiles)} percentile records")
        if len(df_percentiles) > 0:
            print(f"   Metrics: {df_percentiles['metric'].nunique()}")
            print(f"   Peer groups: {df_percentiles['peer_group_name'].nunique()}")
        return df_percentiles

    def save_to_database(self, df_percentiles):
        if len(df_percentiles) == 0:
            print("⚠️ No records to save!")
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS peer_percentiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT,
                peer_group_name TEXT,
                metric TEXT,
                value REAL,
                percentile_rank REAL,
                year INTEGER,
                UNIQUE(company_id, peer_group_name, metric, year)
            )
        """)
        latest_year = df_percentiles['year'].iloc[0]
        cursor.execute("DELETE FROM peer_percentiles WHERE year = ?", (latest_year,))
        df_percentiles.to_sql('peer_percentiles', self.conn, if_exists='append', index=False)
        self.conn.commit()
        print(f"✅ Saved {len(df_percentiles)} records to peer_percentiles table")
        cursor.execute("SELECT COUNT(*) FROM peer_percentiles WHERE year = ?", (latest_year,))
        count = cursor.fetchone()[0]
        print(f"   Verified: {count} records for year {latest_year}")

    def close(self):
        if self.conn:
            self.conn.close()

    def run(self):
        self.connect()
        try:
            self.load_peer_groups()
            df_financial = self.get_latest_financial_data()
            df_percentiles = self.calculate_percentiles(df_financial)
            self.save_to_database(df_percentiles)
            return df_percentiles
        finally:
            self.close()


if __name__ == "__main__":
    print("="*60)
    print("🚀 PEER ENGINE - DAY 18")
    print("="*60)
    
    peer_engine = PeerEngine()
    df_percentiles = peer_engine.run()
    
    print("\n" + "="*60)
    print("📊 PEER ANALYSIS COMPLETE!")
    print("="*60)
    print(f"Total percentile records: {len(df_percentiles)}")
    
    if len(df_percentiles) > 0:
        print("\n📋 Sample percentile records:")
        print(df_percentiles.head(10))
        
        # Verify database
        conn = sqlite3.connect("nifty100.db")
        df_groups = pd.read_sql("SELECT DISTINCT peer_group_name FROM peer_percentiles", conn)
        print(f"\n📊 Unique peer groups: {len(df_groups)}")
        print(df_groups['peer_group_name'].tolist())
        conn.close()
    else:
        print("⚠️ No percentile records generated!")