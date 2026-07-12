# src/nlp/parser.py
import re, sqlite3, pandas as pd, logging
logger = logging.getLogger(__name__)

# Matches: '10 Years: 21%' | '5 Year: 6%' | '10Years:21%'
CAGR_PATTERN = re.compile(r'(\d+)\s*[Yy]ears?:?\s*([\d.]+)%')

TEXT_COLS = ['compounded_sales_growth','compounded_profit_growth',
             'stock_price_cagr','roe']


def parse_cagr_text(text):
    """Extract [(n_years, cagr_pct)] from one text cell.
    '10 Years: 21%\n5 Years: 18%' -> [(10, 21.0), (5, 18.0)]
    """
    if not isinstance(text, str) or not text.strip(): return []
    return [(int(m.group(1)), float(m.group(2)))
            for m in CAGR_PATTERN.finditer(text)]


def parse_analysis_table(db_path):
    """Parse all text fields in analysis table -> long-format DataFrame."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql('SELECT * FROM analysis', conn); conn.close()

    records = []
    for _, row in df.iterrows():
        cid = row['company_id']
        for col in TEXT_COLS:
            if col not in row or pd.isna(row[col]): continue
            parsed = parse_cagr_text(str(row[col]))
            if not parsed:
                logger.warning(f'No CAGR match in {col} for {cid}: {row[col]!r}')
            for n, cagr in parsed:
                records.append({'company_id':cid,'metric_type':col,
                                 'period_years':n,'value_pct':cagr})

    result = pd.DataFrame(records)
    result.to_csv('output/analysis_parsed.csv', index=False)
    logger.info(f'Parsed {len(result)} CAGR values from {df.company_id.nunique()} companies')
    return result


def cross_validate_cagr(parsed_df, db_path, tolerance_pct=5.0):
    """Compare parsed CAGR vs Ratio Engine CAGR. Flag >5% divergence."""
    conn = sqlite3.connect(db_path)
    ratios = pd.read_sql(
        'SELECT company_id,revenue_cagr_5yr,revenue_cagr_10yr,pat_cagr_5yr FROM financial_ratios',
        conn); conn.close()

    latest = ratios.groupby('company_id').last().reset_index()
    col_map = {('compounded_sales_growth',5):'revenue_cagr_5yr',
               ('compounded_sales_growth',10):'revenue_cagr_10yr',
               ('compounded_profit_growth',5):'pat_cagr_5yr'}

    flags = []
    for _, pr in parsed_df.iterrows():
        rc = col_map.get((pr['metric_type'], pr['period_years']))
        if not rc: continue
        r = latest[latest['company_id']==pr['company_id']]
        if r.empty or pd.isna(r[rc].iloc[0]): continue
        diff = abs(pr['value_pct'] - r[rc].iloc[0])
        if diff > tolerance_pct:
            flags.append({**pr.to_dict(),'ratio_engine':r[rc].iloc[0],'divergence':diff})

    result = pd.DataFrame(flags)
    result.to_csv('output/cross_validation.csv', index=False)
    return result

# cross_validate_cagr catches both calculation bugs AND genuine data discrepancies -
# review every flagged row.
