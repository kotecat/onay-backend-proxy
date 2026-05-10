"""
All upstream HTTP services live here.
Each function wraps a specific upstream call and can modify
the request before sending or the response before returning.
"""
from __future__ import annotations
from pathlib import Path

import httpx
from fastapi import Request

from config import settings


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
