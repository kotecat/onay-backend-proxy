import logging
from colorlog import ColoredFormatter
from config import settings


formatter = ColoredFormatter(
    "[%(asctime)s] [ %(log_color)s%(levelname)-5s%(reset)s / %(name)s ]: %(log_color)s%(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
    log_colors={
        "DEBUG":    "cyan",
        "INFO":     "green",
        "WARNING":  "yellow",
        "ERROR":    "red",
        "CRITICAL": "bold_red",
    },
    reset=True,
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

THIRD_PARTY_LOGGERS = [
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "uvicorn.lifespan",
    "fastapi",
    "starlette",
    "httpx",
    "httpcore",
]

for name in THIRD_PARTY_LOGGERS:
    lg = logging.getLogger(name)
    lg.handlers.clear()
    lg.propagate = True
