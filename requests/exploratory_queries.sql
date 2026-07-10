-- Total Companies
SELECT COUNT(*) FROM companies;

-- Total Market Cap Records
SELECT COUNT(*) FROM market_cap;

-- Highest ROE
SELECT
    company_name,
    roe_percentage
FROM companies
ORDER BY roe_percentage DESC
LIMIT 10;

-- Highest ROCE
SELECT
    company_name,
    roce_percentage
FROM companies
ORDER BY roce_percentage DESC
LIMIT 10;

-- Top Market Cap Companies
SELECT
    c.company_name,
    MAX(m.market_cap_crore) AS market_cap
FROM market_cap m
JOIN companies c
ON c.id = m.company_id
GROUP BY c.company_name
ORDER BY market_cap DESC
LIMIT 10;

-- Sector Distribution
SELECT
    broad_sector,
    COUNT(*) AS companies
FROM sectors
GROUP BY broad_sector
ORDER BY companies DESC;

-- Average PE Ratio
SELECT
    AVG(pe_ratio)
FROM market_cap;

-- Companies With Highest Debt
SELECT
    company_id,
    MAX(total_debt_cr) AS debt
FROM financial_ratios
GROUP BY company_id
ORDER BY debt DESC
LIMIT 10;