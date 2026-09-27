PRAGMA foreign_keys = ON;


CREATE TABLE IF NOT EXISTS companies (

    company_id INTEGER PRIMARY KEY,

    ticker TEXT UNIQUE NOT NULL,

    company_name TEXT NOT NULL,

    sector_id INTEGER

);



CREATE TABLE sectors (

    id INTEGER PRIMARY KEY,

    ticker TEXT,

    broad_sector TEXT,

    sub_sector TEXT,

    index_weight_pct REAL,

    market_cap_category TEXT

);



CREATE TABLE IF NOT EXISTS profitandloss (

    pnl_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    year INTEGER,

    sales REAL,

    operating_profit REAL,

    net_profit REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS balancesheet (

    bs_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    year INTEGER,

    equity_capital REAL,

    reserves REAL,

    borrowings REAL,

    other_liabilities REAL,

    total_liabilities REAL,

    total_assets REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS cashflow (

    cf_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    year INTEGER,

    operating_cashflow REAL,

    investing_cashflow REAL,

    financing_cashflow REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS analysis (

    analysis_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    summary TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS documents (

    document_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    url TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS prosandcons (

    id INTEGER PRIMARY KEY,

    company_id INTEGER,

    pros TEXT,

    cons TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS stock_prices (

    price_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    date TEXT,

    close_price REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

);



CREATE TABLE IF NOT EXISTS financial_ratios (

    ratio_id INTEGER PRIMARY KEY,

    company_id TEXT,

    year INTEGER,

    net_profit_margin_pct REAL,

    operating_profit_margin_pct REAL,

    return_on_assets_pct REAL,

    return_on_equity_pct REAL,

    debt_to_equity REAL,

    asset_turnover REAL,

    free_cash_flow_cr REAL,

    cash_from_operations_cr REAL,

    revenue_cagr_5yr REAL,

    pat_cagr_5yr REAL

);



CREATE TABLE IF NOT EXISTS peer_groups (

    peer_id INTEGER PRIMARY KEY,

    company_id INTEGER,

    peer_company TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(company_id)

)