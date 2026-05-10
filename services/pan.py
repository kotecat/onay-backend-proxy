import logging

from fastapi import Request

from .proxy import client, _proxy_headers


logger = logging.getLogger(__name__)


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
        pan = card.get("pan")
        logger.debug(f"Getting card with PAN {pan} for request {request.url}")
        return pan
    
    return None
