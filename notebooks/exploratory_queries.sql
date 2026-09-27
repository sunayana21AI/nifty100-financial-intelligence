-- 1. Total companies
SELECT COUNT(*) AS total_companies
FROM companies;


-- 2. Companies with sectors
SELECT 
c.ticker,
s.sector_name
FROM companies c
LEFT JOIN sectors s
ON c.sector_id = s.sector_id
LIMIT 10;


-- 3. Highest sales companies
SELECT 
c.ticker,
p.sales
FROM profitandloss p
JOIN companies c
ON p.company_id = c.company_id
ORDER BY p.sales DESC
LIMIT 10;


-- 4. Latest profit data
SELECT
c.ticker,
p.year,
p.net_profit
FROM profitandloss p
JOIN companies c
ON p.company_id = c.company_id
ORDER BY p.net_profit DESC
LIMIT 10;


-- 5. Stock price range
SELECT
c.ticker,
MIN(sp.close_price) AS lowest_price,
MAX(sp.close_price) AS highest_price
FROM stock_prices sp
JOIN companies c
ON sp.company_id = c.company_id
GROUP BY c.ticker
LIMIT 10;


-- 6. Balance sheet check
SELECT
c.ticker,
b.total_assets,
b.total_liabilities
FROM balancesheet b
JOIN companies c
ON b.company_id=c.company_id
LIMIT 10;


-- 7. Cashflow summary
SELECT
c.ticker,
SUM(cf.operating_cashflow) AS total_operating_cf
FROM cashflow cf
JOIN companies c
ON cf.company_id=c.company_id
GROUP BY c.ticker
LIMIT 10;


-- 8. Year coverage
SELECT
c.ticker,
COUNT(p.year) AS years_available
FROM companies c
LEFT JOIN profitandloss p
ON c.company_id=p.company_id
GROUP BY c.company_id
ORDER BY years_available;


-- 9. Companies having less than 5 years data
SELECT
c.ticker,
COUNT(p.year) AS years
FROM companies c
LEFT JOIN profitandloss p
ON c.company_id=p.company_id
GROUP BY c.company_id
HAVING years < 5;


-- 10. Foreign key validation
PRAGMA foreign_key_check;