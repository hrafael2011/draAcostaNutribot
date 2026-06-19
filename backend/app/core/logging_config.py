"""Structured JSON logging for production, plain text for development."""
import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(is_production: bool) -> None:
    root = logging.getLogger()
    # Remove any existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if is_production:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(levelname)-8s %(name)-24s %(message)s",
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Quieter client libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
