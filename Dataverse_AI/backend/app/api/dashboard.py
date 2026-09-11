from fastapi import APIRouter

from app.evidence import (
    load_business_kpis, load_top_zones, load_top_od_pairs,
    load_demand_opportunities, load_forecast_opportunities, load_contract,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis")
def kpis():
    return {"kpis": load_business_kpis()}


@router.get("/top-zones")
def top_zones():
    return {"zones": load_top_zones()}


@router.get("/od-pairs")
def od_pairs():
    return {"pairs": load_top_od_pairs()}


@router.get("/demand-opportunities")
def demand_opportunities():
    return {"opportunities": load_demand_opportunities()}


@router.get("/forecast-opportunities")
def forecast_opportunities():
    return {"opportunities": load_forecast_opportunities()}


@router.get("/contract")
def contract():
    return load_contract()
