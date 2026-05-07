"""
Catch-all proxy router.
Every request not matched by overrides.py is forwarded
transparently to the upstream backend.
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from services import forward_request

router = APIRouter(tags=["proxy"])

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

_SKIP_RESPONSE_HEADERS = {
    "content-length",    # chunked streaming — длина неизвестна
    "connection",        # hop-by-hop
    "server",
    "date"
}


@router.api_route("/{path:path}", methods=PROXY_METHODS)
async def catch_all(path: str, request: Request):
    upstream = await forward_request(request, path)

    headers = {
        k: v
        for k, v in upstream.headers.multi_items()
        if k.lower() not in _SKIP_RESPONSE_HEADERS
    }

    return StreamingResponse(
        content=upstream.aiter_raw(),
        status_code=upstream.status_code,
        headers=headers,
        media_type=upstream.headers.get("content-type"),
    )
