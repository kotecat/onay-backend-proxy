"""
All upstream HTTP services live here.
Each function wraps a specific upstream call and can modify
the request before sending or the response before returning.
"""
from __future__ import annotations

import httpx
from pathlib import Path
from fastapi import Request

from config import settings

from time import time
import json


base_storage = Path(settings.ORDER_DIRECTORY)
base_storage.mkdir(parents=True, exist_ok=True)


# ── Shared async client (created once, reused everywhere) ────────────────────

def _build_client() -> httpx.AsyncClient:
    headers = {}

    return httpx.AsyncClient(
        base_url=settings.TARGET_BASE_URL,
        headers=headers,
        timeout=settings.REQUEST_TIMEOUT,
        follow_redirects=True,
    )


client: httpx.AsyncClient = _build_client()


async def close_client() -> None:
    await client.aclose()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _proxy_headers(request: Request) -> dict[str, str]:
    """Strip hop-by-hop headers that must not be forwarded."""
    skip = {
        "host",              # httpx подставит свой из base_url
        "content-length",    # httpx пересчитает сам
    }
    return {k: v for k, v in request.headers.items() if k.lower() not in skip}


# ── Generic passthrough ───────────────────────────────────────────────────────

async def forward_request(request: Request, path: str) -> httpx.Response:
    """
    Transparently forward any request to the upstream backend.
    Preserves method, headers, query params, and body.
    """
    url = httpx.URL(
        path=f"/{path}",
        query=request.url.query.encode(),
    )
    upstream_req = client.build_request(
        method=request.method,
        url=url,
        headers=_proxy_headers(request),
        content=await request.body(),
    )
    return await client.send(upstream_req, stream=True)



async def get_card_pan_by_token(request: Request) -> str | None:
    response = await client.get(
        "/v2/external/customer/cards?cityId=2",
        headers=_proxy_headers(request),
    )
    response.raise_for_status()
    data: dict = response.json()
    
    result = data.get("result", {})
    result_data = result.get("data", [])
    
    if not result_data:
        return None
    
    for card in result_data:
        return card.get("pan", None)
    
    return None


async def get_tickets(request: Request) -> dict:
    response = await client.get(
        "/v2/external/customer/tickets",
        headers=_proxy_headers(request),
        params=dict(request.query_params),
    )
    response.raise_for_status()

    data: dict = response.json()
    
    pan = await get_card_pan_by_token(request)
    
    if pan:
        try:
            path = base_storage / f"pan_{pan}.json"
            
            with open(path, "r", encoding="utf-8") as f:
                order = json.load(f)
        except FileNotFoundError:
            order = None
        if order:
            data["result"]["data"].append(order)
    
    return data


async def start_qr_payment(request: Request, city_id: int) -> dict:
    response = await client.put(
        f"/v1/external/customer/card/acquiring/qr/start?cityId={city_id}",
        headers=_proxy_headers(request),
        content=await request.body(),
    )
    response.raise_for_status()

    data: dict = response.json()
    
    pan = await get_card_pan_by_token(request)
    
    if pan:
        data_payment = data.get("result", {}).get("data", {})
        
        order = {
            "id": int(time()),
            "type": "QR",
            "userInfo": None,
            "payload": {
            "pan": pan,
            "sid": data_payment.get("sessionId", ""),
            "cost": data_payment.get("terminal", {}).get("cost", 0),
            "owner": None,
            "route": data_payment.get("terminal", {}).get("route", ""),
            "cityId": 2,
            "isPass": False,
            "ticket": int(time()).to_bytes(length=4, signed=False).hex()[-5:].upper(),
            "groupKey": "ca2a35ec4f",
            "terminal": data_payment.get("terminal", {}).get("tid", ""),
            "conductor": data_payment.get("terminal", {}).get("conductor", ""),
            "createdAt": data_payment.get("serverDate", ""),
            "routeType": data_payment.get("terminal", {}).get("routeType", 0),
            "updatedAt": data_payment.get("serverDate", ""),
            "ticketInfo": {
                "number": data_payment.get("sessionId", "")[10:32].upper(),
                "series": data_payment.get("sessionId", "")[:10].upper(),
            },
            "completedAt": data_payment.get("serverDate", ""),
            "description": "Поездка в автобусе",
            "agentTransactionId": data_payment.get("agentTransactionId", "")
            },
            "createdAt": data_payment.get("serverDate", ""),
        }
        
        path = base_storage / f"pan_{pan}.json"
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(order, f, ensure_ascii=False, indent=2)
    
    return data
