# Performance Notes — Day 43


## SQLite Indexes

- balancesheet.idx_bs_company_year
- cashflow.idx_cf_company_year
- documents.idx_docs_company
- financial_ratios.idx_ratios_company_year
- financial_ratios.idx_ratios_year
- peer_percentiles.idx_peers_group
- profitandloss.idx_pl_company_year

## DB Query Times

- Latest ratios for TCS: 1.52ms
- All companies count: 0.0ms
- Screener filter: 1.01ms

## Concurrent Screener API Calls

- Total time: 0.215s
- Success: 10/10
- Errors: 0
- Status: PASS