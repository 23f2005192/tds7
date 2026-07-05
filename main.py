from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid
import logging
import json
from collections import deque

app = FastAPI()

# Startup time
START_TIME = time.time()

# Keep last 1000 logs
LOG_BUFFER = deque(maxlen=1000)

# Prometheus counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# JSON logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Count every request
    http_requests_total.inc()

    response = await call_next(request)

    entry = {
        "level": "INFO",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": request.url.path,
        "request_id": request_id,
    }

    LOG_BUFFER.append(entry)
    logger.info(json.dumps(entry))

    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/work")
def work(n: int = 1):
    # Simulate work
    total = 0
    for i in range(n):
        total += i

    return {
        "email": "YOUR_EMAIL@example.com",
        "done": n
    }


@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest().decode(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/logs/tail")
def tail(limit: int = 10):
    limit = max(1, min(limit, len(LOG_BUFFER)))
    return JSONResponse(list(LOG_BUFFER)[-limit:])