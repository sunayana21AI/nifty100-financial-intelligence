"""
Day 21: Data Quality Unit Tests
14 DQ rule unit tests
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "nifty100.db"


class DataQualityTests:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.results = []
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def run_test(self, test_name, test_func):
        """Run a single test and record result"""
        try:
            result = test_func()
            self.results.append({
                'test': test_name,
                'status': 'PASS' if result else 'FAIL',
                'details': str(result) if result is True else str(result)
            })
            return result
        except Exception as e:
            self.results.append({
                'test': test_name,
                'status': 'FAIL',
                'details': str(e)
            })
            return False
    
    # -------- 1. Table Existence Tests --------
    
    def test_companies_table_exists(self):
        """Test 1: companies table exists"""
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'", self.conn)
        return len(df) > 0
    
    def test_financial_ratios_table_exists(self):
        """Test 2: financial_ratios table exists"""
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='financial_ratios'", self.conn)
        return len(df) > 0
    
    def test_peer_percentiles_table_exists(self):
        """Test 3: peer_percentiles table exists"""
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='peer_percentiles'", self.conn)
        return len(df) > 0
    
    # -------- 2. Data Completeness Tests --------
    
    def test_financial_ratios_has_data(self):
        """Test 4: financial_ratios has data"""
        df = pd.read_sql("SELECT COUNT(*) as count FROM financial_ratios", self.conn)
        return df['count'].iloc[0] > 0
    
    def test_latest_year_has_companies(self):
        """Test 5: Latest year has at least 50 companies"""
        df = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM financial_ratios 
            WHERE year = (SELECT MAX(year) FROM financial_ratios)
        """, self.conn)
        return df['count'].iloc[0] >= 50
    
    def test_roe_not_null(self):
        """Test 6: ROE has data for latest year"""
        df = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM financial_ratios 
            WHERE year = (SELECT MAX(year) FROM financial_ratios)
            AND return_on_equity_pct IS NOT NULL
        """, self.conn)
        return df['count'].iloc[0] > 0
    
    def test_debt_to_equity_not_null(self):
        """Test 7: Debt to Equity has data"""
        df = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM financial_ratios 
            WHERE debt_to_equity IS NOT NULL
        """, self.conn)
        return df['count'].iloc[0] > 0
    
    # -------- 3. Peer Percentile Tests --------
    
    def test_peer_percentiles_has_data(self):
        """Test 8: peer_percentiles has data"""
        df = pd.read_sql("SELECT COUNT(*) as count FROM peer_percentiles", self.conn)
        return df['count'].iloc[0] > 0
    
    def test_peer_percentiles_has_10_metrics(self):
        """Test 9: peer_percentiles has all 10 metrics"""
        df = pd.read_sql("""
            SELECT COUNT(DISTINCT metric) as count 
            FROM peer_percentiles
        """, self.conn)
        return df['count'].iloc[0] == 10
    
    def test_peer_percentiles_has_11_groups(self):
        """Test 10: peer_percentiles has 11 peer groups"""
        df = pd.read_sql("""
            SELECT COUNT(DISTINCT peer_group_name) as count 
            FROM peer_percentiles
        """, self.conn)
        return df['count'].iloc[0] == 11
    
    def test_peer_percentiles_2024_data(self):
        """Test 11: peer_percentiles has 2024 data"""
        df = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM peer_percentiles 
            WHERE year = 2024
        """, self.conn)
        return df['count'].iloc[0] > 0
    
    # -------- 4. Data Quality Tests --------
    
    def test_roe_percentile_range(self):
        """Test 12: ROE percentiles are between 0 and 1"""
        df = pd.read_sql("""
            SELECT percentile_rank 
            FROM peer_percentiles 
            WHERE metric = 'return_on_equity_pct'
        """, self.conn)
        if len(df) == 0:
            return False
        return (df['percentile_rank'] >= 0).all() and (df['percentile_rank'] <= 1).all()
    
    def test_de_percentile_range(self):
        """Test 13: D/E percentiles are between 0 and 1"""
        df = pd.read_sql("""
            SELECT percentile_rank 
            FROM peer_percentiles 
            WHERE metric = 'debt_to_equity'
        """, self.conn)
        if len(df) == 0:
            return False
        return (df['percentile_rank'] >= 0).all() and (df['percentile_rank'] <= 1).all()
    
    def test_composite_score_exists(self):
        """Test 14: composite_quality_score exists in financial_ratios"""
        try:
            df = pd.read_sql("""
                SELECT COUNT(*) as count 
                FROM financial_ratios 
                WHERE composite_quality_score IS NOT NULL
            """, self.conn)
            return df['count'].iloc[0] > 0
        except:
            return False
    
    def run_all_tests(self):
        """Run all 14 tests"""
        self.connect()
        
        tests = [
            ('1. companies table exists', self.test_companies_table_exists),
            ('2. financial_ratios table exists', self.test_financial_ratios_table_exists),
            ('3. peer_percentiles table exists', self.test_peer_percentiles_table_exists),
            ('4. financial_ratios has data', self.test_financial_ratios_has_data),
            ('5. Latest year has >=50 companies', self.test_latest_year_has_companies),
            ('6. ROE has data', self.test_roe_not_null),
            ('7. Debt to Equity has data', self.test_debt_to_equity_not_null),
            ('8. peer_percentiles has data', self.test_peer_percentiles_has_data),
            ('9. peer_percentiles has 10 metrics', self.test_peer_percentiles_has_10_metrics),
            ('10. peer_percentiles has 11 groups', self.test_peer_percentiles_has_11_groups),
            ('11. peer_percentiles has 2024 data', self.test_peer_percentiles_2024_data),
            ('12. ROE percentiles in 0-1 range', self.test_roe_percentile_range),
            ('13. D/E percentiles in 0-1 range', self.test_de_percentile_range),
            ('14. composite_quality_score exists', self.test_composite_score_exists),
        ]
        
        print("="*60)
        print("📊 DATA QUALITY UNIT TESTS")
        print("="*60)
        
        passed = 0
        for test_name, test_func in tests:
            result = self.run_test(test_name, test_func)
            if result:
                passed += 1
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} - {test_name}")
        
        print("\n" + "="*60)
        print(f"📊 RESULTS: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 ALL TESTS PASSED! ✅")
        else:
            print(f"⚠️ {len(tests) - passed} tests failed")
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f"   ❌ {r['test']}: {r['details']}")
        
        self.close()
        return passed == len(tests)
    
    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    dq = DataQualityTests()
    dq.run_all_tests()