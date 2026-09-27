"""
Day 20: Peer Comparison Excel Summary
Generates professional Excel report with peer group comparisons
"""

import sqlite3
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DB_PATH = "nifty100.db"
OUTPUT_FILE = Path("output/peer_comparison.xlsx")


class PeerComparisonReport:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
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
        self.metric_labels = {
            'return_on_equity_pct': 'ROE',
            'return_on_capital_employed_pct': 'ROCE',
            'net_profit_margin_pct': 'NPM',
            'debt_to_equity': 'D/E',
            'free_cash_flow_cr': 'FCF',
            'pat_cagr_5yr': 'PAT CAGR',
            'revenue_cagr_5yr': 'Revenue CAGR',
            'eps_cagr_5yr': 'EPS CAGR',
            'interest_coverage': 'Interest Coverage',
            'asset_turnover': 'Asset Turnover'
        }
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def get_peer_groups(self):
        """Get list of all peer groups"""
        query = """
        SELECT DISTINCT peer_group_name 
        FROM peer_percentiles 
        ORDER BY peer_group_name
        """
        df = pd.read_sql(query, self.conn)
        return df['peer_group_name'].tolist()
    
    def get_peer_group_data(self, peer_group):
        """Get all data for a specific peer group"""
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
            c.ticker,
            s.broad_sector,
            p.percentile_rank as roe_percentile,
            p2.percentile_rank as roce_percentile,
            p3.percentile_rank as npm_percentile,
            p4.percentile_rank as de_percentile,
            p5.percentile_rank as fcf_percentile,
            p6.percentile_rank as pat_cagr_percentile,
            p7.percentile_rank as revenue_cagr_percentile,
            p8.percentile_rank as eps_cagr_percentile,
            p9.percentile_rank as ic_percentile,
            p10.percentile_rank as asset_turnover_percentile
        FROM financial_ratios f
        JOIN companies c ON f.company_id = c.ticker
        LEFT JOIN sectors s ON f.company_id = s.ticker
        LEFT JOIN peer_percentiles p ON f.company_id = p.company_id AND p.metric = 'return_on_equity_pct'
        LEFT JOIN peer_percentiles p2 ON f.company_id = p2.company_id AND p2.metric = 'return_on_capital_employed_pct'
        LEFT JOIN peer_percentiles p3 ON f.company_id = p3.company_id AND p3.metric = 'net_profit_margin_pct'
        LEFT JOIN peer_percentiles p4 ON f.company_id = p4.company_id AND p4.metric = 'debt_to_equity'
        LEFT JOIN peer_percentiles p5 ON f.company_id = p5.company_id AND p5.metric = 'free_cash_flow_cr'
        LEFT JOIN peer_percentiles p6 ON f.company_id = p6.company_id AND p6.metric = 'pat_cagr_5yr'
        LEFT JOIN peer_percentiles p7 ON f.company_id = p7.company_id AND p7.metric = 'revenue_cagr_5yr'
        LEFT JOIN peer_percentiles p8 ON f.company_id = p8.company_id AND p8.metric = 'eps_cagr_5yr'
        LEFT JOIN peer_percentiles p9 ON f.company_id = p9.company_id AND p9.metric = 'interest_coverage'
        LEFT JOIN peer_percentiles p10 ON f.company_id = p10.company_id AND p10.metric = 'asset_turnover'
        WHERE f.year = (SELECT MAX(year) FROM financial_ratios)
        AND s.broad_sector = ?
        AND f.company_id IN (
            SELECT DISTINCT company_id 
            FROM peer_percentiles 
            WHERE peer_group_name = ?
        )
        ORDER BY f.return_on_equity_pct DESC
        """
        
        df = pd.read_sql(query, self.conn, params=(peer_group, peer_group))
        return df
    
    def prepare_dataframe(self, df):
        """Prepare DataFrame with metric values and percentiles"""
        
        # Select columns for output
        cols = ['company_id', 'company_name']
        
        # Add metric values and percentiles
        for metric in self.metrics:
            label = self.metric_labels.get(metric, metric)
            cols.append(metric)
            cols.append(f'{metric}_percentile')
        
        # Filter to existing columns
        cols = [c for c in cols if c in df.columns]
        
        df_result = df[cols].copy()
        
        # Rename percentile columns to readable names
        rename_map = {}
        for metric in self.metrics:
            label = self.metric_labels.get(metric, metric)
            if f'{metric}_percentile' in df_result.columns:
                rename_map[f'{metric}_percentile'] = f'{label} Percentile'
            if metric in df_result.columns:
                rename_map[metric] = label
        
        df_result = df_result.rename(columns=rename_map)
        
        return df_result
    
    def add_benchmark_row(self, df, ticker='TCS'):
        """Add benchmark company highlight"""
        # Check if benchmark exists in dataframe
        if ticker in df['company_id'].values:
            df['is_benchmark'] = df['company_id'] == ticker
        else:
            df['is_benchmark'] = False
        return df
    
    def get_peer_median(self, df):
        """Calculate median for each metric in peer group"""
        medians = {}
        for metric in self.metrics:
            label = self.metric_labels.get(metric, metric)
            if label in df.columns:
                medians[label] = df[label].median()
        return medians
    
    def apply_conditional_formatting(self, workbook, sheet_name):
        """Apply conditional formatting based on percentile ranks"""
        ws = workbook[sheet_name]
        
        # Find percentile columns
        percentile_cols = []
        for col in range(1, ws.max_column + 1):
            cell_value = ws.cell(row=1, column=col).value
            if cell_value and 'Percentile' in str(cell_value):
                percentile_cols.append(col)
        
        # Apply formatting
        for col in percentile_cols:
            col_letter = get_column_letter(col)
            for row in range(2, ws.max_row + 1):
                cell = ws[f'{col_letter}{row}']
                value = cell.value
                if value is not None:
                    try:
                        val = float(value)
                        if val >= 0.75:
                            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Green
                            cell.font = Font(color="006100")
                        elif val <= 0.25:
                            cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Red
                            cell.font = Font(color="9C0006")
                        else:
                            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Yellow
                            cell.font = Font(color="9C6500")
                    except:
                        pass
    
    def highlight_benchmark(self, workbook, sheet_name, ticker='TCS'):
        """Highlight benchmark company row"""
        ws = workbook[sheet_name]
        
        # Find company_id column
        company_col = None
        for col in range(1, ws.max_column + 1):
            if ws.cell(row=1, column=col).value == 'company_id':
                company_col = col
                break
        
        if company_col:
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=company_col)
                if cell.value == ticker:
                    # Highlight entire row
                    for col in range(1, ws.max_column + 1):
                        cell = ws.cell(row=row, column=col)
                        cell.fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")  # Gold
                        cell.font = Font(bold=True)
                    break
    
    def generate_report(self, benchmark_ticker='TCS'):
        """Generate complete peer comparison report"""
        
        self.connect()
        
        print("📊 Generating Peer Comparison Report...")
        
        # Get peer groups
        peer_groups = self.get_peer_groups()
        print(f"   Found {len(peer_groups)} peer groups")
        
        # Create Excel writer
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            
            for peer_group in peer_groups:
                print(f"   Processing: {peer_group}")
                
                # Get data
                df = self.get_peer_group_data(peer_group)
                if len(df) == 0:
                    print(f"      ⚠️ No data for {peer_group}")
                    continue
                
                # Prepare DataFrame
                df_prepared = self.prepare_dataframe(df)
                
                # Add benchmark flag
                df_prepared = self.add_benchmark_row(df_prepared, benchmark_ticker)
                
                # Calculate medians
                medians = self.get_peer_median(df_prepared)
                
                # Write to Excel
                sheet_name = peer_group[:31]  # Excel sheet name max 31 chars
                df_prepared.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get workbook and add summary row
                workbook = writer.book
                ws = workbook[sheet_name]
                
                # Add median row at bottom
                median_row = ws.max_row + 1
                
                # Write "Peer Median" in first column
                ws.cell(row=median_row, column=1, value="Peer Median")
                ws.cell(row=median_row, column=1).font = Font(bold=True)
                
                # Write median values
                for col_idx, col_name in enumerate(df_prepared.columns, start=1):
                    if col_name in medians:
                        ws.cell(row=median_row, column=col_idx, value=medians[col_name])
                        ws.cell(row=median_row, column=col_idx).font = Font(bold=True)
                
                # Apply formatting
                self.apply_conditional_formatting(workbook, sheet_name)
                
                # Highlight benchmark
                self.highlight_benchmark(workbook, sheet_name, benchmark_ticker)
                
                # Auto-adjust column widths
                for col in ws.columns:
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 40)
                    ws.column_dimensions[column].width = adjusted_width
        
        print(f"\n✅ Report generated: {OUTPUT_FILE}")
        print(f"   Total sheets: {len(peer_groups)}")
        
        self.close()
        return OUTPUT_FILE
    
    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    print("="*60)
    print("🚀 DAY 20 — PEER COMPARISON EXCEL SUMMARY")
    print("="*60)
    
    report = PeerComparisonReport()
    report.generate_report(benchmark_ticker='TCS')
    
    print("\n✅ Peer Comparison Report generated successfully!")