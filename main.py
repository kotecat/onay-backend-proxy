import log_config
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import settings
from services import proxy as proxy_service
from routers import overrides, proxy
import services


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=settings.LOG_LEVEL,
    handlers=[log_config.handler],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastAPI application...")
    yield
    logger.info("Shutting down FastAPI application...")
    await proxy_service.close_client()
    logger.info("FastAPI application shutdown complete.")

app = FastAPI(
    title="Reverse Proxy",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)


# ── Routers (order matters: overrides first, catch-all last) ──────────────────

if settings.FAKE_PAYMENT_ENABLED:
    app.include_router(overrides.fp_router)
app.include_router(proxy.router)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
