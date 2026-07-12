# tests/kpi/test_ratios.py
import pytest
from src.analytics.ratios import (
    net_profit_margin, roe, debt_to_equity,
    interest_coverage_ratio, free_cash_flow, revenue_cagr
)

def test_npm_positive(): assert net_profit_margin(100,500) == pytest.approx(20.0)
def test_npm_zero_sales(): assert net_profit_margin(100,0) is None
def test_npm_neg_profit(): assert net_profit_margin(-50,500) == pytest.approx(-10.0)

@pytest.mark.parametrize('np_v,eq,res,expected',[
    (100, 10, 490, 20.0),   # standard
    (100,-100, 50, None),   # negative equity -> None
    (0, 10, 490, 0.0),      # zero profit
])
def test_roe(np_v, eq, res, expected):
    result = roe(np_v, eq, res)
    if expected is None: assert result is None
    else: assert result == pytest.approx(expected, rel=0.01)

def test_de_zero_debt(): assert debt_to_equity(0, 500) == 0.0
def test_de_standard(): assert debt_to_equity(250, 500) == pytest.approx(0.5)
def test_de_neg_equity(): assert debt_to_equity(100, -50) is None

def test_icr_zero_interest(): assert interest_coverage_ratio(5000,0,200) is None
def test_icr_normal(): assert interest_coverage_ratio(5000,500,200) == pytest.approx(5.2)

def test_fcf_positive(): assert free_cash_flow(500,-200) == 300
def test_fcf_negative(): assert free_cash_flow(-100,-200) == -300

@pytest.mark.parametrize('start,end,n,exp_val,exp_flag',[
    (100, 161.05, 5, 10.0, None),
    (-100, 200, 5, None, 'TURNAROUND'),
    (100, -50, 5, None, 'DECLINE_TO_LOSS'),
    (-100, -50, 5, None, 'BOTH_NEGATIVE'),
    (0, 100, 5, None, 'ZERO_BASE'),
    (100, 130, 2, None, 'INSUFFICIENT'),
])
def test_cagr_edge_cases(start, end, n, exp_val, exp_flag):
    val, flag = revenue_cagr(start, end, n)
    if exp_val is None: assert val is None and flag == exp_flag
    else: assert val == pytest.approx(exp_val, rel=0.01)

# pytest.approx(rel=0.01): 1% relative tolerance - essential for floating-point CAGR
# comparisons.
