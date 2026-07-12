# src/analytics/cashflow_kpis.py
import sqlite3, pandas as pd, numpy as np, logging
logger = logging.getLogger(__name__)

PATTERNS = {
    ('+','-','-'): 'Reinvestor',
    ('+','-','+'): 'Growth Funded',
    ('+','+','-'): 'Shareholder Returns',
    ('+','+','+'): 'Asset Liquidation',
    ('-','-','+'): 'Distress',
    ('-','+','+'): 'Turnaround Attempt',
    ('-','-','-'): 'Declining',
    ('-','+','-'): 'Restructuring',
}

def _sign(val): return '+' if (not pd.isna(val) and val >= 0) else '-'

def classify_capital_allocation(row):
    key = (_sign(row['operating_activity']),
           _sign(row['investing_activity']),
           _sign(row['financing_activity']))
    return PATTERNS.get(key, 'Unknown')

def cfo_quality_score(cfo, pat):
    """Returns (ratio, label). >1.0=High Quality, 0.5-1.0=Moderate, <0.5=Accrual Risk."""
    if pd.isna(pat) or pat == 0: return None, 'N/A'
    ratio = cfo / pat
    label = 'High Quality' if ratio > 1.0 else ('Moderate' if ratio > 0.5 else 'Accrual Risk')
    return round(ratio, 4), label

def capex_intensity(investing_activity, sales):
    """abs(CFI)/sales*100 -> (pct, tier). <3%=Asset-Light, 3-8%=Moderate, >8%=Capital Intensive."""
    if pd.isna(sales) or sales == 0 or pd.isna(investing_activity): return None, 'N/A'
    pct = abs(investing_activity) / sales * 100
    tier = 'Asset-Light' if pct < 3 else ('Moderate' if pct < 8 else 'Capital Intensive')
    return round(pct, 4), tier

def fcf_cagr(fcf_series, n):
    """FCF CAGR over n years. Returns None on turnaround, negative base, or insufficient history."""
    s = fcf_series.dropna().sort_index()
    if len(s) < n + 1: return None
    end_v, start_v = s.iloc[-1], s.iloc[-(n+1)]
    if start_v <= 0 or end_v <= 0: return None  # turnaround / both negative
    return round(((end_v / start_v) ** (1/n) - 1) * 100, 4)

def detect_distress(group):
    """CFO<0 AND CFF>0 = raising funds to cover operating losses."""
    d = group[(group['operating_activity'] < 0) & (group['financing_activity'] > 0)].copy()
    d['distress_flag'] = 'Distress Signal'
    return d

def build_cashflow_intelligence(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    df = pd.read_sql("""
        SELECT cf.company_id, cf.year,
               cf.operating_activity, cf.investing_activity,
               cf.financing_activity, cf.net_cash_flow,
               pl.net_profit, pl.sales, pl.operating_profit,
               bs.borrowings
        FROM cashflow cf
        JOIN profitandloss pl USING (company_id, year)
        JOIN balancesheet bs USING (company_id, year)
    """, conn); conn.close()

    df['capital_pattern'] = df.apply(classify_capital_allocation, axis=1)

    quality = df.apply(lambda r: cfo_quality_score(r.operating_activity, r.net_profit), axis=1)
    df[['cfo_pat_ratio','cfo_quality_label']] = pd.DataFrame(quality.tolist(), index=df.index)

    capex = df.apply(lambda r: capex_intensity(r.investing_activity, r.sales), axis=1)
    df[['capex_intensity_pct','capex_tier']] = pd.DataFrame(capex.tolist(), index=df.index)

    df['fcf_cr'] = df['operating_activity'] + df['investing_activity']

    cagrs = []
    for cid, grp in df.groupby('company_id'):
        s = grp.set_index('year')['fcf_cr']
        cagrs.append({'company_id': cid,
                       'fcf_cagr_5yr': fcf_cagr(s, 5),
                       'fcf_cagr_10yr': fcf_cagr(s, 10)})
    df = df.merge(pd.DataFrame(cagrs), on='company_id', how='left')

    # Export
    df.to_excel('output/cashflow_intelligence.xlsx', index=False)

    distress_rows = pd.concat([detect_distress(g) for _, g in df.groupby('company_id')])
    distress_rows.to_csv('output/distress_alerts.csv', index=False)

    logger.info(f'CF Intelligence: {len(df)} rows, {len(distress_rows)} distress events')
    return df

# The 8-pattern dict is the cleanest implementation: a 3-sign tuple becomes the exact dict key.
#
# WHY CFO/PAT > 1.0 SIGNALS HIGH-QUALITY EARNINGS
# Net profit (PAT) is an accrual figure - it includes income earned but not yet collected. When CFO
# exceeds PAT, the company collects cash faster than it recognises profit - a sign of high earnings
# quality. When CFO/PAT < 0.5 consistently, the profit is mostly accrual and the business is not
# converting earnings into real cash. This CFO/PAT ratio is one of the most powerful quality signals
# in fundamental analysis.
