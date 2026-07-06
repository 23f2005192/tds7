from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from collections import deque
import logging
import json
import time
import uuid

app = FastAPI()

# IMPORTANT: No trailing period
EMAIL = "23f2005192@ds.study.iitm.ac.in"

START_TIME = time.time()

# Store last 1000 log entries
LOG_BUFFER = deque(maxlen=1000)

# Prometheus counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# Logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


@app.middleware("http")
async def metrics_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Increment counter for every request
    http_requests_total.inc()

    response = await call_next(request)

    log = {
        "level": "INFO",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": request.url.path,
        "request_id": request_id,
    }

    LOG_BUFFER.append(log)
    logger.info(json.dumps(log))

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/work")
async def work(n: int = 1):
    # Simulate work
    _ = sum(range(n))

    return {
        "email": EMAIL,
        "done": n
    }


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(
        generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }


@app.get("/logs/tail")
async def logs_tail(limit: int = 10):
    limit = max(1, min(limit, len(LOG_BUFFER)))
    return list(LOG_BUFFER)[-limit:]
