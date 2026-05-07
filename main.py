import uvicorn
from fastapi import FastAPI

from config import settings
from services import close_client
from routers import overrides, proxy

app = FastAPI(
    title="Reverse Proxy",
    docs_url="/proxy-docs" if settings.APP_DEBUG else None,
    redoc_url=None,
)

# ── Lifespan events ───────────────────────────────────────────────────────────

@app.on_event("shutdown")
async def on_shutdown():
    await close_client()


# ── Routers (order matters: overrides first, catch-all last) ──────────────────

app.include_router(overrides.router)
app.include_router(proxy.router)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
