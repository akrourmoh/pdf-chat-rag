"""Observability: structured logging, request tracing, and error tracking.

- Every log line includes a short request id, so all logs for one request can
  be grouped together (tracing).
- Optional Sentry integration: if SENTRY_DSN is set, errors are reported there.
"""

import logging
from contextvars import ContextVar

import config

# Holds the current request's id (set by the request-logging middleware).
request_id_var = ContextVar("request_id", default="-")

logger = logging.getLogger("pdfchat")


def _record_factory(old_factory):
    # Attach the current request id to every log record.
    def factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id_var.get()
        return record

    return factory


def configure_logging():
    # Set up a single, clean log format. Called once at startup.
    if logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] [req:%(request_id)s] %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logging.setLogRecordFactory(_record_factory(logging.getLogRecordFactory()))


def init_error_tracking():
    # Enable Sentry only if a DSN is configured and the package is available.
    dsn = config.SENTRY_DSN
    if not dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn, environment=config.ENVIRONMENT)
        logger.info("Sentry error tracking enabled")
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("Could not initialise Sentry: %s", exc)
