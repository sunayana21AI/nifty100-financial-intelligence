# check_excel_structure.py
import pandas as pd

# Read your Excel file
df = pd.read_excel('data/raw/financial_ratios.xlsx')

print("=== EXCEL FILE STRUCTURE ===")
print(f"Shape: {df.shape}")
print(f"\nColumns:\n{df.columns.tolist()}")
print(f"\nFirst 3 rows:\n{df.head(3)}")

# Check for ROE columns
roe_cols = [col for col in df.columns if 'ROE' in str(col) or 'Equity' in str(col) or 'Mar' in str(col)]
print(f"\nPotential ROE/year columns: {roe_cols}")

# Show sample ROE values
for col in roe_cols[:5]:
    print(f"\nColumn '{col}':")
    sample = df[col].dropna().head(5)
    print(sample)
    print(f"Data type: {df[col].dtype}")