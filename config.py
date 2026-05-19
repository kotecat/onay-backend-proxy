import logging
from decouple import config


class Settings:
    # ── Upstream ──────────────────────────────────────────────
    TARGET_BASE_URL: str = config("TARGET_BASE_URL")

    # ── App ───────────────────────────────────────────────────
    APP_HOST: str = config("APP_HOST", default="0.0.0.0")
    APP_PORT: int = config("APP_PORT", default=8000, cast=int)
    APP_DEBUG: bool = config("APP_DEBUG", default=True, cast=bool)
    APP_WORKERS: int = config("APP_WORKERS", default=2, cast=int)
    LOG_LEVEL: int = getattr(logging, config("LOG_LEVEL", default="INFO"))

    # ── HTTP client ───────────────────────────────────────────
    REQUEST_TIMEOUT: float = config("REQUEST_TIMEOUT", default=30.0, cast=float)
    
    ORDER_DIRECTORY: str = config("ORDER_DIRECTORY", default="./orders")
    FAKE_PAYMENT_ENABLED: bool = config("FAKE_PAYMENT_ENABLED", default=True, cast=bool)

settings = Settings()
