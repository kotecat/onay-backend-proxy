"""
Overridden routes.
Matched BEFORE the catch-all proxy router — intercept specific
endpoints here to modify requests or responses.
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from services import get_tickets, start_qr_payment

router = APIRouter(tags=["overrides"])


@router.get("/v2/external/customer/tickets")
async def get_tickets_endpoint(request: Request):
    data = await get_tickets(request)
    return JSONResponse(content=data)


@router.put("/v1/external/customer/card/acquiring/qr/start")
async def start_qr_payment_endpoint(request: Request, cityId: int = Query(...)):
    data = await start_qr_payment(request, city_id=cityId)
    return JSONResponse(content=data)