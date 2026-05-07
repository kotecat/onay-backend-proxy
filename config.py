from decouple import config, Csv


class Settings:
    # ── Upstream ──────────────────────────────────────────────
    TARGET_BASE_URL: str = config("TARGET_BASE_URL")

    # ── App ───────────────────────────────────────────────────
    APP_HOST: str = config("APP_HOST", default="0.0.0.0")
    APP_PORT: int = config("APP_PORT", default=8000, cast=int)
    APP_DEBUG: bool = config("APP_DEBUG", default=False, cast=bool)

    # ── HTTP client ───────────────────────────────────────────
    REQUEST_TIMEOUT: float = config("REQUEST_TIMEOUT", default=30.0, cast=float)
    
    ORDER_DIRECTORY: str = config("ORDER_DIRECTORY", default="./orders")


settings = Settings()
