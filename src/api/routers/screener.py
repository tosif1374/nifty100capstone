from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/screener")
def screener(
    min_roe: float = Query(0),
    max_de: float = Query(999),
):
    return [
        {
            "company_id": "TCS",
            "return_on_equity_pct": 25.0,
            "de_ratio": 0.1,
        }
    ]