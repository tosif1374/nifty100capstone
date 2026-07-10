DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS profit_and_loss;
DROP TABLE IF EXISTS balance_sheet;
DROP TABLE IF EXISTS cash_flow;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS pros_and_cons;

CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

CREATE TABLE analysis (
    id INTEGER,
    company_id TEXT,
    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL
);

CREATE TABLE balance_sheet (
    id INTEGER,
    company_id TEXT,
    year INTEGER,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL
);

CREATE TABLE cash_flow (
    id INTEGER,
    company_id TEXT,
    year INTEGER,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL
);

CREATE TABLE documents (
    id INTEGER,
    company_id TEXT,
    Year INTEGER,
    Annual_Report TEXT
);

CREATE TABLE financial_ratios (
    id INTEGER,
    company_id TEXT,
    year INTEGER,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL
);

CREATE TABLE market_cap (
    id INTEGER,
    company_id TEXT,
    year INTEGER,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL
);

CREATE TABLE peer_groups (
    id INTEGER,
    peer_group_name TEXT,
    company_id TEXT,
    is_benchmark INTEGER
);

CREATE TABLE profit_and_loss (
    id INTEGER,
    company_id TEXT,
    year INTEGER,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL
);

CREATE TABLE pros_and_cons (
    id INTEGER,
    company_id TEXT,
    pros TEXT,
    cons TEXT
);

CREATE TABLE sectors (
    id INTEGER,
    company_id TEXT,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT
);

CREATE TABLE stock_prices (
    id INTEGER,
    company_id TEXT,
    date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    adjusted_close REAL
);