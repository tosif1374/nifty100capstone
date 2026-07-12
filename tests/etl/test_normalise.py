# tests/etl/test_normalise.py
import pytest
from src.etl.normaliser import normalize_year, normalize_ticker

@pytest.mark.parametrize('raw,expected', [
    ('Mar-23', '2023-03'), ('Mar 23', '2023-03'),
    ('March-2023','2023-03'), ('FY23', '2023-03'),
    ('FY2023', '2023-03'), ('fy23', '2023-03'),  # lowercase
    ('2023', '2023-03'), (2023, '2023-03'),      # int input
    ('Dec-22', '2022-12'), ('Jun-23', '2023-06'),
    ('Sep-22', '2022-09'), ('2023-03', '2023-03'),  # pass-through
    ('2022-23', '2023-03'), ('2022-2023','2023-03'),
    (' Mar-23 ', '2023-03'), (' 2023 ', '2023-03'),
])
def test_normalize_year_valid(raw, expected):
    assert normalize_year(raw) == expected

@pytest.mark.parametrize('raw',['garbage','',' ','YEAR23','99','10000'])
def test_normalize_year_invalid_raises(raw):
    with pytest.raises((ValueError, KeyError)):
        normalize_year(raw)

@pytest.mark.parametrize('raw,expected',[
    ('TCS','TCS'),('tcs','TCS'),(' TCS ','TCS'),
    ('INFY.NS','INFY'),('infy.ns','INFY'),
    ('BAJAJ-AUTO','BAJAJ-AUTO'),('M&M','M&M'),
    ('HDFCBANK.BO','HDFCBANK'),(' SBIN ','SBIN'),
])
def test_normalize_ticker_valid(raw, expected):
    assert normalize_ticker(raw) == expected

def test_normalize_ticker_rejects_empty():
    with pytest.raises(ValueError): normalize_ticker('')

def test_normalize_ticker_rejects_too_long():
    with pytest.raises(ValueError): normalize_ticker('VERYLONGTICKERNAME')
