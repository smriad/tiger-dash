#!/usr/bin/env python3
"""Tiny API that reads pre-aggregated metrics from the continuous aggregate."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg

QUERY = """
SELECT bucket, sensor_id, metric,
       sample_count,
       avg_value, min_value, max_value
FROM ghw_sensor_hourly
WHERE bucket >= now() - make_interval(hours => $1::int)
  AND ($2::text IS NULL OR sensor_id = $2)
ORDER BY bucket DESC, sensor_id, metric
LIMIT 200
"""


def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL (tiger connection string for stillbench)")
    return psycopg.connect(url)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/metrics":
            qs = parse_qs(parsed.query)
            hours = int(qs.get("hours", ["24"])[0])
            sensor = qs.get("sensor", [None])[0]
            with get_conn() as conn:
                rows = conn.execute(QUERY, (hours, sensor)).fetchall()
            body = [
                {
                    "bucket": r[0].isoformat(),
                    "sensor_id": r[1],
                    "metric": r[2],
                    "sample_count": r[3],
                    "avg_value": float(r[4]) if r[4] is not None else None,
                    "min_value": float(r[5]) if r[5] is not None else None,
                    "max_value": float(r[6]) if r[6] is not None else None,
                }
                for r in rows
            ]
            import json

            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path in ("/", "/index.html"):
            path = os.path.join(os.path.dirname(__file__), "index.html")
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404)

    def log_message(self, fmt, *args):
        return


def main():
    port = int(os.environ.get("PORT", "8765"))
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
