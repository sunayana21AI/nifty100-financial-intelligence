\# Sprint 2 — Financial Ratio Engine Retrospective



\## Sprint Goal

Build a financial ratio engine capable of computing profitability,

growth, leverage, efficiency and cash flow KPIs for all Nifty100 companies.



\## Completed Work



\### Profitability Ratios

Implemented:

\- Net Profit Margin

\- Operating Profit Margin

\- Return on Assets

\- Return on Equity framework

\- Return on Capital Employed framework



\### Leverage \& Efficiency

Implemented:

\- Debt-to-Equity framework

\- Interest Coverage

\- Net Debt framework

\- Asset Turnover



\### CAGR Engine

Implemented:

\- Revenue CAGR

\- PAT CAGR

\- EPS CAGR



Handled edge cases:

\- Positive to Positive

\- Positive to Negative

\- Negative to Positive turnaround

\- Both negative

\- Zero base

\- Insufficient data



\### Cash Flow KPIs

Implemented:

\- Free Cash Flow

\- CFO Quality Score

\- CapEx Intensity

\- FCF Conversion

\- Capital Allocation Classification



\## Validation



\- Total KPI tests passed: 42

\- Companies processed: 92

\- Financial ratio records generated: 1073



\## Data Limitations



The available source dataset did not contain:



\- Borrowings

\- Equity Capital

\- Reserves

\- ROE benchmark column

\- ROCE benchmark column



Therefore:

\- Exact Debt-to-Equity calculation was limited

\- ROE and ROCE comparison with source values was not possible



All limitations were documented in ratio\_edge\_cases.log.



\## Final Status



Sprint 2 completed successfully.

All available KPI calculations validated through automated tests.

