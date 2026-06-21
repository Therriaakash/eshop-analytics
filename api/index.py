from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "telemetry.json")

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile95(values):
    values = sorted(values)
    n = len(values)

    if n == 0:
        return 0

    pos = 0.95 * (n - 1)
    lower = int(pos)
    upper = min(lower + 1, n - 1)

    if lower == upper:
        return values[lower]

    fraction = pos - lower
    return values[lower] + fraction * (values[upper] - values[lower])


@app.get("/")
def home():
    response = JSONResponse(content={"status": "ok"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def calculate_metrics(req: AnalyticsRequest):
    result = {}

    for region in req.regions:
        rows = [r for r in telemetry if r["region"] == region]

        if not rows:
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(percentile95(latencies), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(
                1 for x in latencies
                if x > req.threshold_ms
            )
        }

    return result


@app.post("/")
def analytics_root(req: AnalyticsRequest):
    result = calculate_metrics(req)
    response = JSONResponse(content=result)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.post("/analytics")
def analytics(req: AnalyticsRequest):
    result = calculate_metrics(req)
    response = JSONResponse(content=result)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.options("/")
def options_root():
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.options("/analytics")
def options_analytics():
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
