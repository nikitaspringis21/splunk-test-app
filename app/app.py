"""Small demo web shop that writes JSON logs for Splunk.

Log file: /var/log/webapp/app.log (one JSON object per line)
"""
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

LOG_FILE = os.environ.get("WEBAPP_LOG", "/var/log/webapp/app.log")

app = Flask(__name__)

PRODUCTS = [
    {"id": 1, "name": "Keyboard", "price": 49.90, "stock": 12},
    {"id": 2, "name": "Mouse", "price": 19.90, "stock": 40},
    {"id": 3, "name": "Monitor", "price": 189.00, "stock": 5},
    {"id": 4, "name": "Headset", "price": 79.50, "stock": 0},
]
USERS = {"alice": "wonderland", "bob": "builder", "admin": "S3cure!"}


# ---------- logging ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        event = {
            "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event.update(getattr(record, "fields", {}))
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event)


log = logging.getLogger("webapp")
log.setLevel(logging.INFO)
_handler = logging.FileHandler(LOG_FILE)
_handler.setFormatter(JsonFormatter())
log.addHandler(_handler)


def client_ip():
    # nginx passes the real client address in X-Real-IP
    return request.headers.get("X-Real-IP", request.remote_addr)


def emit(level, message, **fields):
    base = {
        "request_id": getattr(g, "request_id", None),
        "client_ip": client_ip(),
        "method": request.method,
        "path": request.path,
    }
    base.update(fields)
    log.log(level, message, extra={"fields": base})


@app.before_request
def start_timer():
    g.start = time.perf_counter()
    g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex


@app.after_request
def log_request(response):
    duration_ms = round((time.perf_counter() - g.start) * 1000, 2)
    level = logging.ERROR if response.status_code >= 500 else (
        logging.WARNING if response.status_code >= 400 else logging.INFO)
    emit(level, "request completed", status=response.status_code,
         duration_ms=duration_ms, user_agent=request.headers.get("User-Agent"))
    response.headers["X-Request-ID"] = g.request_id
    return response


# ---------- routes ----------
@app.get("/")
def index():
    return jsonify(app="demo-shop", endpoints=[
        "GET /health", "GET /api/products", "GET /api/products/<id>",
        "POST /api/login", "POST /api/orders", "GET /api/slow", "GET /api/error"])


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/products")
def products():
    return jsonify(PRODUCTS)


@app.get("/api/products/<int:pid>")
def product(pid):
    item = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not item:
        emit(logging.WARNING, "product not found", product_id=pid)
        return jsonify(error="not found"), 404
    return jsonify(item)


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    user = data.get("username", "")
    ok = USERS.get(user) == data.get("password")
    emit(logging.INFO if ok else logging.WARNING,
         "login success" if ok else "login failed",
         event_type="auth", user=user, action="success" if ok else "failure")
    if not ok:
        return jsonify(error="invalid credentials"), 401
    return jsonify(token=uuid.uuid4().hex)


@app.post("/api/orders")
def order():
    data = request.get_json(silent=True) or {}
    pid, qty = data.get("product_id"), int(data.get("quantity", 1))
    item = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not item:
        return jsonify(error="unknown product"), 400
    if item["stock"] < qty:
        emit(logging.WARNING, "order rejected: out of stock", event_type="order",
             product_id=pid, quantity=qty, stock=item["stock"])
        return jsonify(error="out of stock"), 409
    order_id = uuid.uuid4().hex[:10]
    total = round(item["price"] * qty, 2)
    emit(logging.INFO, "order placed", event_type="order", order_id=order_id,
         product_id=pid, product=item["name"], quantity=qty, amount=total)
    return jsonify(order_id=order_id, amount=total), 201


@app.get("/api/slow")
def slow():
    delay = random.uniform(0.5, 3.0)
    time.sleep(delay)
    emit(logging.WARNING, "slow operation", delay_s=round(delay, 2))
    return jsonify(waited=round(delay, 2))


@app.get("/api/error")
def error():
    try:
        raise RuntimeError("database connection lost")
    except RuntimeError:
        log.exception("unhandled error", extra={"fields": {
            "request_id": g.request_id, "client_ip": client_ip(), "path": request.path}})
        return jsonify(error="internal server error"), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
