"""
Day 19: Peer Radar Charts
Generates radar charts for companies vs their peer group average
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = "nifty100.db"
OUTPUT_DIR = Path("reports/radar_charts")


class RadarGenerator:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        # 7 metrics (composite removed)
        self.metrics = [
            'return_on_equity_pct',
            'return_on_capital_employed_pct',
            'net_profit_margin_pct',
            'debt_to_equity',
            'free_cash_flow_cr',
            'pat_cagr_5yr',
            'revenue_cagr_5yr'
        ]
        self.metric_labels = [
            'ROE',
            'ROCE',
            'NPM',
            'D/E (inv)',
            'FCF',
            'PAT CAGR',
            'Revenue CAGR'
        ]
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def get_company_data(self, ticker):
        """Get company data for radar chart"""
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
            f.asset_turnover,
            f.interest_coverage,
            c.company_name,
            c.ticker,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category
        FROM financial_ratios f
        JOIN companies c ON f.company_id = c.ticker
        LEFT JOIN sectors s ON f.company_id = s.ticker
        WHERE f.company_id = ?
        AND f.year = (SELECT MAX(year) FROM financial_ratios)
        """
        
        df = pd.read_sql(query, self.conn, params=(ticker,))
        if len(df) == 0:
            return None
        return df.iloc[0]
    
    def get_peer_group_avg(self, company_data):
        """Get peer group average for metrics"""
        if pd.isna(company_data['broad_sector']):
            return None
        
        peer_group = company_data['broad_sector']
        
        query = """
        SELECT 
            AVG(f.return_on_equity_pct) as return_on_equity_pct,
            AVG(f.return_on_capital_employed_pct) as return_on_capital_employed_pct,
            AVG(f.net_profit_margin_pct) as net_profit_margin_pct,
            AVG(f.debt_to_equity) as debt_to_equity,
            AVG(f.free_cash_flow_cr) as free_cash_flow_cr,
            AVG(f.pat_cagr_5yr) as pat_cagr_5yr,
            AVG(f.revenue_cagr_5yr) as revenue_cagr_5yr,
            COUNT(*) as company_count
        FROM financial_ratios f
        JOIN companies c ON f.company_id = c.ticker
        LEFT JOIN sectors s ON f.company_id = s.ticker
        WHERE s.broad_sector = ?
        AND f.year = (SELECT MAX(year) FROM financial_ratios)
        """
        
        df = pd.read_sql(query, self.conn, params=(peer_group,))
        if len(df) == 0 or df.iloc[0]['company_count'] < 2:
            return None
        
        return df.iloc[0]
    
    def get_nifty_avg(self):
        """Get Nifty 100 average for reference"""
        query = """
        SELECT 
            AVG(f.return_on_equity_pct) as return_on_equity_pct,
            AVG(f.return_on_capital_employed_pct) as return_on_capital_employed_pct,
            AVG(f.net_profit_margin_pct) as net_profit_margin_pct,
            AVG(f.debt_to_equity) as debt_to_equity,
            AVG(f.free_cash_flow_cr) as free_cash_flow_cr,
            AVG(f.pat_cagr_5yr) as pat_cagr_5yr,
            AVG(f.revenue_cagr_5yr) as revenue_cagr_5yr
        FROM financial_ratios f
        WHERE f.year = (SELECT MAX(year) FROM financial_ratios)
        """
        
        df = pd.read_sql(query, self.conn)
        if len(df) == 0:
            return None
        return df.iloc[0]
    
    def prepare_data_for_radar(self, company_data, peer_data, nifty_data=None):
        """Prepare data for radar chart"""
        
        # For D/E, we want inverse (lower is better)
        def inverse_de(de_value):
            if pd.isna(de_value) or de_value < 0:
                return 0
            return 1 / (1 + de_value)
        
        # Prepare company values
        company_values = []
        for metric in self.metrics:
            val = company_data.get(metric, 0)
            if metric == 'debt_to_equity':
                val = inverse_de(val) * 100
            elif pd.isna(val):
                val = 0
            else:
                val = float(val)
            company_values.append(val)
        
        # Prepare peer values
        peer_values = []
        if peer_data is not None:
            for metric in self.metrics:
                val = peer_data.get(metric, 0)
                if metric == 'debt_to_equity':
                    val = inverse_de(val) * 100
                elif pd.isna(val):
                    val = 0
                else:
                    val = float(val)
                peer_values.append(val)
        else:
            peer_values = [0] * len(self.metrics)
        
        # Prepare Nifty values
        nifty_values = []
        if nifty_data is not None:
            for metric in self.metrics:
                val = nifty_data.get(metric, 0)
                if metric == 'debt_to_equity':
                    val = inverse_de(val) * 100
                elif pd.isna(val):
                    val = 0
                else:
                    val = float(val)
                nifty_values.append(val)
        else:
            nifty_values = [0] * len(self.metrics)
        
        return company_values, peer_values, nifty_values
    
    def generate_radar_chart(self, ticker, company_values, peer_values, nifty_values, 
                             company_name, peer_group):
        """Generate and save radar chart"""
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        N = len(self.metrics)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        
        company_values += company_values[:1]
        peer_values += peer_values[:1]
        nifty_values += nifty_values[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        # Nifty average
        if sum(nifty_values[:-1]) > 0:
            ax.plot(angles, nifty_values, 'o-', linewidth=1, linestyle='--', 
                   color='gray', alpha=0.5, label='Nifty 100 Avg')
            ax.fill(angles, nifty_values, alpha=0.1, color='gray')
        
        # Peer average
        if sum(peer_values[:-1]) > 0:
            ax.plot(angles, peer_values, 'o-', linewidth=2, linestyle='--', 
                   color='blue', alpha=0.7, label=f'{peer_group} Avg')
            ax.fill(angles, peer_values, alpha=0.15, color='blue')
        
        # Company
        ax.plot(angles, company_values, 'o-', linewidth=2.5, color='red', 
               label=ticker)
        ax.fill(angles, company_values, alpha=0.25, color='red')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.metric_labels, fontsize=10)
        
        max_val = max(max(company_values), max(peer_values) if sum(peer_values[:-1]) > 0 else 0,
                     max(nifty_values) if sum(nifty_values[:-1]) > 0 else 0)
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 100)
        ax.grid(True, alpha=0.3)
        
        title = f"{company_name} ({ticker})"
        if peer_group and not pd.isna(peer_group):
            title += f"\nPeer Group: {peer_group}"
        else:
            title += "\n(No Peer Group - Nifty 100 Reference)"
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
        
        plt.tight_layout()
        filename = f"{ticker}_radar.png"
        filepath = OUTPUT_DIR / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_for_company(self, ticker):
        self.connect()
        try:
            company_data = self.get_company_data(ticker)
            if company_data is None:
                print(f"❌ Company not found: {ticker}")
                return None
            
            company_name = company_data['company_name']
            peer_group = company_data['broad_sector']
            
            print(f"📊 Generating radar for {ticker} - {company_name}")
            
            peer_data = None
            if not pd.isna(peer_group):
                peer_data = self.get_peer_group_avg(company_data)
                if peer_data is not None:
                    print(f"   Peer Group: {peer_group} ({int(peer_data['company_count'])} companies)")
                else:
                    print(f"   Peer Group: {peer_group} (insufficient data)")
            
            nifty_data = self.get_nifty_avg()
            if nifty_data is not None:
                print("   Using Nifty 100 average as reference")
            
            company_values, peer_values, nifty_values = self.prepare_data_for_radar(
                company_data, peer_data, nifty_data
            )
            
            filepath = self.generate_radar_chart(
                ticker, company_values, peer_values, nifty_values,
                company_name, peer_group
            )
            
            print(f"   ✅ Saved: {filepath}")
            return filepath
            
        finally:
            self.close()
    
    def generate_for_all(self, tickers=None):
        if tickers is None:
            self.connect()
            query = """
            SELECT DISTINCT company_id 
            FROM financial_ratios 
            WHERE year = (SELECT MAX(year) FROM financial_ratios)
            """
            df = pd.read_sql(query, self.conn)
            tickers = df['company_id'].tolist()
            self.close()
        
        print(f"📊 Generating radar charts for {len(tickers)} companies...")
        results = []
        
        for ticker in tickers:
            try:
                result = self.generate_for_company(ticker)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"❌ Error generating for {ticker}: {e}")
                continue
        
        print(f"\n✅ Generated {len(results)} radar charts in {OUTPUT_DIR}")
        return results
    
    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    print("="*60)
    print("🚀 DAY 19 — RADAR CHART GENERATOR")
    print("="*60)
    
    generator = RadarGenerator()
    
    # Generate for specific companies
    specific_companies = ['TCS', 'INFY', 'HDFCBANK', 'BEL', 'RELIANCE']
    generator.generate_for_all(specific_companies)
    
    print("\n✅ Radar charts generated successfully!")