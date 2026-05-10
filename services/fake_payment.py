import json
import logging
from pathlib import Path
from time import time
from random import randbytes

from fastapi import Request

from config import settings
from .proxy import client, _proxy_headers
from .pan import get_card_pan_by_token


base_storage = Path(settings.ORDER_DIRECTORY)
base_storage.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


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
            logger.debug(f"Loading order for PAN {pan} from {path}")
            with open(path, "r", encoding="utf-8") as f:
                order = json.load(f)
        except FileNotFoundError:
            logger.debug(f"No order found for PAN {pan} at {path}")
            order = None
        if order:
            payload = order.get("payload", {})
            data["result"]["data"].append(order)
            logger.info(
                f"Added order "
                f"term={payload.get('terminal')} "
                f"bus={payload.get('conductor')} "
                f"route={payload.get('route')} "
                f"city={payload.get('cityId')} "
                f"cost={round(int(payload.get('cost')) / 100, 2)} "
                f"for PAN {pan} to response data"
            )
    
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
                "groupKey": randbytes(5).hex(),
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
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(order, f, ensure_ascii=False, indent=2)
                logger.info(
                    f"Saved order "
                    f"term={order['payload'].get('terminal')} "
                    f"bus={order['payload'].get('conductor')} "
                    f"route={order['payload'].get('route')} "
                    f"city={order['payload'].get('cityId')} "
                    f"cost={round(int(order['payload'].get('cost', 0)) / 100, 2)} "
                    f"for PAN {pan} to {path}"
                )
        except Exception as e:
            logger.error(f"Failed to save order for PAN {pan} to {path}: {e}")
            
    
    return data
