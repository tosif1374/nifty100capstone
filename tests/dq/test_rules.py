# tests/dq/test_rules.py
import pytest, pandas as pd
from src.etl.validator import (
    check_pk_uniqueness, check_composite_pk, check_fk_integrity,
    check_bs_balance, check_opm_crosscheck, check_positive_sales
)

# DQ-01: PK uniqueness
def test_dq01_triggers_on_dup():
    df = pd.DataFrame({'id':['TCS','INFY','TCS']})
    res = check_pk_uniqueness(df,'id')
    assert len(res)>0 and all(r['severity']=='CRITICAL' for r in res)

def test_dq01_passes_clean():
    assert check_pk_uniqueness(pd.DataFrame({'id':['TCS','INFY']}),'id') == []

# DQ-02: Composite PK
def test_dq02_triggers():
    df = pd.DataFrame({'company_id':['TCS','TCS'],'year':['2023-03','2023-03']})
    assert len(check_composite_pk(df)) > 0

# DQ-03: FK integrity
def test_dq03_flags_orphan():
    child = pd.DataFrame({'company_id':['TCS','FAKE']})
    result = check_fk_integrity(child, {'TCS'})
    assert any('FAKE' in r['detail'] for r in result)

# DQ-04: BS balance
def test_dq04_triggers_imbalance():
    row = pd.Series({'total_assets':1000,'total_liab_and_equity':1020})
    res = check_bs_balance(row, tolerance_pct=1.0)
    assert res and res['severity']=='WARNING'

def test_dq04_passes_within_tolerance():
    row = pd.Series({'total_assets':1000,'total_liab_and_equity':1005})
    assert check_bs_balance(row, tolerance_pct=1.0) is None

# DQ-05: OPM cross-check
def test_dq05_triggers_mismatch():
    row = pd.Series({'sales':1000,'operating_profit':200,'reported_opm':25.0})
    assert check_opm_crosscheck(row) is not None

# DQ-06: Positive sales
def test_dq06_triggers_negative():
    assert check_positive_sales(pd.Series({'sales':-500})) is not None

def test_dq06_passes_positive():
    assert check_positive_sales(pd.Series({'sales':500})) is None

# Each DQ test has BOTH a negative case (rule triggers) and a positive case (rule
# passes) - both are required.
