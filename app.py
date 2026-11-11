"""
Egg Production API
------------------
A REST API for a poultry farmer in Kiambu with three sheds. Log each shed's
daily egg count, then pull all records with running totals - no more adding
up WhatsApp messages on Saturday.

Pages:
    /                 web form: log a record and see all records + totals update live

Endpoints:
    POST /api/eggs    log a daily record: {"shed": "A", "date": "2026-11-09", "count": 412}
    GET  /api/eggs    all records (oldest first) with a running total, plus totals per shed
                      optional filters: ?shed=A  ?from=2026-11-09  ?to=2026-11-15

CORS: the web page is served by this same Flask app, so it needs no CORS.
If a separate frontend (e.g. VS Code Live Server on port 5500) calls the API,
list its address in ALLOWED_ORIGINS in .env, comma-separated.

Optional security: set EGG_API_KEY in a .env file and every request must send
the header  X-API-Key: <your key>.

Usage:
    pip install -r requirements.txt
    python app.py
"""

import os
from datetime import date, datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)

SHEDS = ["A", "B", "C"]          # the farm's three sheds
MAX_DAILY_COUNT = 5000           # sanity limit per shed per day
API_KEY = os.getenv("EGG_API_KEY", "").strip()
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if ALLOWED_ORIGINS:
    # Only these other websites may call the API from a browser - never "*" in production.
    CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

records = []                     # in-memory store (resets when the server restarts)
next_id = 1


# ---------------------------------------------------------------- helpers

def error(message, status):
    return jsonify({"error": message}), status


def parse_date(value, field):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"'{field}' must be a date in YYYY-MM-DD format, e.g. 2026-11-09")


def normalise_shed(value):
    shed = str(value).strip().upper().replace("SHED", "").strip()
    if shed not in SHEDS:
        raise ValueError(f"Unknown shed '{value}'. Use one of: {', '.join(SHEDS)}")
    return shed


@app.before_request
def check_api_key():
    if API_KEY and request.path.startswith("/api/") and request.headers.get("X-API-Key") != API_KEY:
        return error("Invalid or missing API key. Send it in the X-API-Key header.", 401)


# ---------------------------------------------------------------- pages

@app.route("/")
def home():
    return render_template("index.html", sheds=SHEDS, today=date.today().isoformat(),
                           max_count=MAX_DAILY_COUNT)


# ---------------------------------------------------------------- endpoints

@app.route("/api/eggs", methods=["POST"])
def log_eggs():
    global next_id
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Send JSON like {\"shed\": \"A\", \"date\": \"2026-11-09\", \"count\": 412}", 400)

    missing = [f for f in ("shed", "date", "count") if f not in data]
    if missing:
        return error(f"Missing field(s): {', '.join(missing)}", 400)

    try:
        shed = normalise_shed(data["shed"])
        day = parse_date(data["date"], "date")
    except ValueError as err:
        return error(str(err), 400)
    if day > date.today():
        return error("The date can't be in the future.", 400)

    count = data["count"]
    if isinstance(count, bool) or not isinstance(count, int):
        return error("'count' must be a whole number, e.g. 412", 400)
    if not 0 <= count <= MAX_DAILY_COUNT:
        return error(f"'count' must be between 0 and {MAX_DAILY_COUNT}.", 400)

    if any(r["shed"] == shed and r["date"] == day.isoformat() for r in records):
        return error(f"Shed {shed} already has a record for {day.isoformat()}.", 409)

    record = {"id": next_id, "shed": shed, "date": day.isoformat(), "count": count}
    next_id += 1
    records.append(record)
    return jsonify(record), 201


@app.route("/api/eggs", methods=["GET"])
def list_eggs():
    selected = records
    try:
        if "shed" in request.args:
            shed = normalise_shed(request.args["shed"])
            selected = [r for r in selected if r["shed"] == shed]
        if "from" in request.args:
            start = parse_date(request.args["from"], "from").isoformat()
            selected = [r for r in selected if r["date"] >= start]
        if "to" in request.args:
            end = parse_date(request.args["to"], "to").isoformat()
            selected = [r for r in selected if r["date"] <= end]
    except ValueError as err:
        return error(str(err), 400)

    running = 0
    rows = []
    for r in sorted(selected, key=lambda r: (r["date"], r["shed"])):
        running += r["count"]
        rows.append({**r, "running_total": running})

    by_shed = {s: sum(r["count"] for r in selected if r["shed"] == s) for s in SHEDS}
    return jsonify({
        "records": rows,
        "totals": {
            "by_shed": by_shed,
            "all_sheds": running,
            "records": len(rows),
        },
    }), 200


@app.errorhandler(404)
def not_found(_err):
    return error("Not found. Open / for the web page, or use /api/eggs", 404)


@app.errorhandler(405)
def method_not_allowed(_err):
    return error("Method not allowed. Use GET or POST on /api/eggs", 405)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
