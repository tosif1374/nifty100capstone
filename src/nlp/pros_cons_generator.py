# src/nlp/pros_cons_generator.py
import sqlite3, pandas as pd, logging
logger = logging.getLogger(__name__)

# Each rule: (type, rule_id, text, condition_fn, confidence)
PRO_RULES = [
    ('pro','P01','Consistently high ROE above 20% - strong shareholder returns',
        lambda r: r.get('return_on_equity_pct',0)>20, 90),
    ('pro','P02','Debt-free balance sheet - low financial risk',
        lambda r: r.get('debt_to_equity',1)==0.0, 92),
    ('pro','P03','Positive Free Cash Flow - business generates real cash',
        lambda r: r.get('free_cash_flow_cr',-1)>0, 85),
    ('pro','P04','Revenue CAGR above 15% over 5 years',
        lambda r: r.get('revenue_cagr_5yr',0)>15, 88),
    ('pro','P05','ROCE above 25% - efficient use of capital employed',
        lambda r: r.get('return_on_capital_pct',0)>25, 87),
    ('pro','P06','Interest coverage above 10x - minimal debt servicing risk',
        lambda r: (v:=r.get('interest_coverage')) is not None and v>10, 86),
    ('pro','P07','Net profit margin above 20% - premium pricing power',
        lambda r: r.get('net_profit_margin_pct',0)>20, 83),
    ('pro','P08','High quality earnings: CFO/PAT ratio above 1.0',
        lambda r: (v:=r.get('cfo_pat_ratio')) is not None and v>1.0, 82),
    ('pro','P09','PAT CAGR above 20% over 5 years - accelerating profit growth',
        lambda r: r.get('pat_cagr_5yr',0)>20, 85),
    ('pro','P10','Asset-light business model: CapEx intensity below 3%',
        lambda r: (v:=r.get('capex_intensity_pct',100)) is not None and v<3, 80),
    ('pro','P11','Dividend yield above 2% - steady investor income',
        lambda r: r.get('dividend_yield_pct',0)>2, 75),
    ('pro','P12','Low D/E below 0.5 - safety margin for downturns',
        lambda r: r.get('debt_to_equity',1)<0.5, 80),
]

CON_RULES = [
    ('con','C01','Debt-to-equity above 2.0 - elevated leverage risk',
        lambda r: r.get('debt_to_equity',0)>2.0, 88),
    ('con','C02','Negative Free Cash Flow - cash drain concern',
        lambda r: (v:=r.get('free_cash_flow_cr',1)) is not None and v<0, 85),
    ('con','C03','ROE below 10% - suboptimal return on equity',
        lambda r: (v:=r.get('return_on_equity_pct')) is not None and 0<v<10, 80),
    ('con','C04','Revenue growth below 5% CAGR 5yr',
        lambda r: (v:=r.get('revenue_cagr_5yr')) is not None and v<5, 78),
    ('con','C05','Interest coverage below 2x - debt servicing pressure',
        lambda r: (v:=r.get('interest_coverage')) is not None and 0<v<2, 84),
    ('con','C06','OPM below 10% - thin margins vulnerable to cost inflation',
        lambda r: (v:=r.get('operating_profit_margin_pct')) is not None and v<10, 75),
    ('con','C07','Dividend payout above 100% - paying more than earned',
        lambda r: r.get('dividend_payout_ratio_pct',0)>100, 82),
    ('con','C08','Capital-intensive model: CapEx above 8% of sales',
        lambda r: (v:=r.get('capex_intensity_pct')) is not None and v>8, 77),
    ('con','C09','Negative net profit - company is loss-making',
        lambda r: r.get('net_profit_margin_pct',0)<0, 92),
    ('con','C10','Accrual risk: CFO/PAT ratio below 0.5',
        lambda r: (v:=r.get('cfo_pat_ratio')) is not None and v<0.5, 83),
    ('con','C11','PAT CAGR below 5% over 5yr - profit growth lagging',
        lambda r: (v:=r.get('pat_cagr_5yr')) is not None and v<5, 76),
    ('con','C12','Asset turnover below 0.5 - assets not generating revenue efficiently',
        lambda r: (v:=r.get('asset_turnover')) is not None and v<0.5, 72),
]


def generate_pros_cons(db_path, min_confidence=60,
                        output='output/pros_cons_generated.csv'):
    """Run all 24 rules against latest-year ratios for all 92 companies."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("""
        SELECT r.*, ci.cfo_pat_ratio, ci.capex_intensity_pct,
               m.dividend_yield_pct
        FROM financial_ratios r
        LEFT JOIN cashflow_intelligence ci USING (company_id, year)
        LEFT JOIN market_cap m ON r.company_id=m.company_id
            AND CAST(SUBSTR(r.year,1,4) AS INT)=m.year
        WHERE r.year=(SELECT MAX(year) FROM financial_ratios WHERE company_id=r.company_id)
    """, conn); conn.close()

    records = []
    for _, row in df.iterrows():
        rd = row.to_dict()
        for ptype,rid,text,cond,conf in PRO_RULES+CON_RULES:
            try: triggered = cond(rd)
            except: triggered = False
            if triggered and conf >= min_confidence:
                records.append({'company_id':row['company_id'],'type':ptype,
                                 'rule_id':rid,'text':text,
                                 'confidence_pct':conf,'year':row['year']})

    result = pd.DataFrame(records)
    result.to_csv(output, index=False)
    logger.info(f'Generated {len(result)} entries for {result["company_id"].nunique()} companies')
    return result

# try/except per rule: one broken lambda (e.g. None comparison) does not break an
# entire company's analysis.
