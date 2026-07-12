# src/api/routers/reports.py
#
# NOTE: The source guide (Nifty100 Sprint 5-6 Code Guide) lists this router in the
# directory structure and endpoint reference table for Module 11, but does not
# include its full implementation in the extracted text - only health.py and
# companies.py are given in full. This stub preserves the expected router name/
# import contract so src/api/main.py runs; fill in the routes per the endpoint
# table in companies.py's trailing comment block.

from fastapi import APIRouter

router = APIRouter(tags=['reports'])
