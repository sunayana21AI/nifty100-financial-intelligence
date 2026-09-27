"""
src/nlp/parser.py
Analysis Text Parser - Extracts structured data from analysis.xlsx
"""

import pandas as pd
import re
import sqlite3
from pathlib import Path
import os

DB_PATH = "nifty100.db"
RAW_DIR = Path("data/raw")
ANALYSIS_FILE = RAW_DIR / "analysis.xlsx"
OUTPUT_DIR = Path("output")


class AnalysisParser:
    def __init__(self):
        self.conn = None
        self.pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%')
        
    def connect(self):
        self.conn = sqlite3.connect(DB_PATH)
        return self.conn
    
    def load_analysis_data(self):
        """Load analysis.xlsx with correct parsing"""
        if not ANALYSIS_FILE.exists():
            print(f"❌ Analysis file not found: {ANALYSIS_FILE}")
            return None
        
        try:
            # Read with header=1 (second row as header)
            df = pd.read_excel(ANALYSIS_FILE, header=1)
            
            # Clean column names
            df.columns = df.columns.str.lower().str.strip()
            df.columns = df.columns.str.replace(' ', '_')
            
            print(f"✅ Loaded analysis data: {len(df)} rows")
            print(f"   Columns: {df.columns.tolist()}")
            print(f"\nSample data:")
            print(df.head(10))
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading analysis file: {e}")
            return None
    
    def parse_text_field(self, text, metric_type):
        """Parse text field using regex pattern"""
        if pd.isna(text) or not isinstance(text, str):
            return None
        
        matches = self.pattern.findall(text)
        results = []
        for match in matches:
            period = int(match[0])
            value = float(match[1])
            results.append({
                'metric_type': metric_type,
                'period_years': period,
                'value_pct': value
            })
        return results
    
    def parse_all_texts(self, df):
        """Parse all text fields in analysis.xlsx"""
        results = []
        failures = []
        
        # Define fields to parse
        text_fields = [
            'compounded_sales_growth',
            'compounded_profit_growth',
            'stock_price_cagr',
            'roe'
        ]
        
        for idx, row in df.iterrows():
            # Get company_id
            company_id = row.get('company_id')
            if pd.isna(company_id):
                continue
            
            # Parse each text column
            for field in text_fields:
                if field not in df.columns:
                    continue
                    
                text = row.get(field)
                if pd.isna(text):
                    continue
                
                parsed = self.parse_text_field(str(text), field)
                if parsed:
                    for p in parsed:
                        results.append({
                            'company_id': str(company_id).strip(),
                            'metric_type': p['metric_type'],
                            'period_years': p['period_years'],
                            'value_pct': p['value_pct']
                        })
                else:
                    failures.append({
                        'company_id': str(company_id).strip(),
                        'field': field,
                        'text': str(text)[:100]
                    })
        
        df_results = pd.DataFrame(results)
        df_failures = pd.DataFrame(failures)
        
        print(f"\n✅ Parsed {len(results)} entries")
        print(f"⚠️ {len(failures)} parsing failures")
        
        return df_results, df_failures
    
    def cross_validate_cagr(self, df_parsed):
        """Cross-validate parsed CAGR against computed CAGR from database"""
        if df_parsed.empty:
            print("⚠️ No parsed data to validate")
            return df_parsed, pd.DataFrame()
        
        self.connect()
        
        # Get computed CAGR from financial_ratios
        query = """
        SELECT 
            company_id,
            revenue_cagr_5yr as computed_sales_cagr,
            pat_cagr_5yr as computed_profit_cagr
        FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
        """
        df_computed = pd.read_sql(query, self.conn)
        self.close()
        
        # Merge with parsed data
        df_merged = df_parsed.merge(
            df_computed,
            left_on='company_id',
            right_on='company_id',
            how='left'
        )
        
        # Flag divergences > 5%
        def check_divergence(row):
            metric = row['metric_type']
            parsed = row['value_pct']
            
            if metric == 'compounded_sales_growth':
                computed = row.get('computed_sales_cagr')
            elif metric == 'compounded_profit_growth':
                computed = row.get('computed_profit_cagr')
            else:
                return 'N/A'
            
            if pd.isna(computed):
                return 'No computed data'
            
            diff = abs(parsed - computed)
            if diff > 5:
                return f'Divergence: {diff:.1f}%'
            return 'Match'
        
        df_merged['validation_status'] = df_merged.apply(check_divergence, axis=1)
        
        # Filter divergences
        df_divergences = df_merged[df_merged['validation_status'] != 'Match']
        
        print(f"\n📊 Cross-validation results:")
        print(f"   Total parsed entries: {len(df_merged)}")
        print(f"   Divergences > 5%: {len(df_divergences)}")
        
        return df_merged, df_divergences
    
    def run(self):
        """Run full parsing pipeline"""
        print("="*60)
        print("📊 ANALYSIS TEXT PARSER - DAY 29")
        print("="*60)
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Load data
        df = self.load_analysis_data()
        if df is None or df.empty:
            print("❌ No data loaded")
            return None
        
        # Parse texts
        df_parsed, df_failures = self.parse_all_texts(df)
        
        # Save parsed data
        parsed_path = OUTPUT_DIR / "analysis_parsed.csv"
        df_parsed.to_csv(parsed_path, index=False)
        print(f"✅ Saved: {parsed_path}")
        
        # Save failures
        if not df_failures.empty:
            failures_path = OUTPUT_DIR / "parse_failures.csv"
            df_failures.to_csv(failures_path, index=False)
            print(f"✅ Saved: {failures_path}")
        
        # Cross-validate
        if not df_parsed.empty:
            df_validated, df_divergences = self.cross_validate_cagr(df_parsed)
            
            # Save validation results
            validated_path = OUTPUT_DIR / "parsed_cagr_validated.csv"
            df_validated.to_csv(validated_path, index=False)
            print(f"✅ Saved: {validated_path}")
            
            if not df_divergences.empty:
                divergences_path = OUTPUT_DIR / "cagr_divergences.csv"
                df_divergences.to_csv(divergences_path, index=False)
                print(f"✅ Saved: {divergences_path}")
        else:
            print("⚠️ No parsed data to validate")
        
        print("\n✅ Parsing complete!")
        return df_parsed
    
    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    parser = AnalysisParser()
    parser.run()