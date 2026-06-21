@app.get("/")
def home():
    return {"status": "ok"}

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
            "breaches": sum(1 for x in latencies if x > req.threshold_ms)
        }

    return result

@app.post("/")
def analytics_root(req: AnalyticsRequest):
    return calculate_metrics(req)

@app.post("/analytics")
def analytics(req: AnalyticsRequest):
    return calculate_metrics(req)
