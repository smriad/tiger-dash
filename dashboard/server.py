#!/usr/bin/env python3
"""Tiny API that reads pre-aggregated metrics from the continuous aggregate."""

import html
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg

QUERY = """
SELECT bucket, sensor_id, metric,
       sample_count,
       avg_value, min_value, max_value
FROM ghw_sensor_hourly
WHERE bucket >= now() - make_interval(hours => %s::int)
  AND (%s::text IS NULL OR sensor_id = %s)
ORDER BY bucket DESC, sensor_id, metric
LIMIT 200
"""


def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL (tiger connection string for stillbench)")
    return psycopg.connect(url)


def fetch_metrics(hours: int = 48, sensor: str | None = None):
    with get_conn() as conn:
        return conn.execute(QUERY, (hours, sensor, sensor)).fetchall()


def rows_to_json(rows):
    return [
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


def rows_to_html(rows) -> str:
    if not rows:
        return (
            "<tr><td colspan='7'>No rows yet — run setup_continuous_aggregate.sql "
            "and refresh.</td></tr>"
        )
    lines = []
    for r in rows:
        bucket = html.escape(r[0].isoformat())
        sensor_id = html.escape(r[1])
        metric = html.escape(r[2])
        avg = f"{float(r[4]):.2f}" if r[4] is not None else "—"
        mn = f"{float(r[5]):.2f}" if r[5] is not None else "—"
        mx = f"{float(r[6]):.2f}" if r[6] is not None else "—"
        lines.append(
            f"<tr><td>{bucket}</td><td>{sensor_id}</td><td>{metric}</td>"
            f"<td>{r[3]}</td><td>{avg}</td><td>{mn}</td><td>{mx}</td></tr>"
        )
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/metrics":
            qs = parse_qs(parsed.query)
            hours = int(qs.get("hours", ["24"])[0])
            sensor = qs.get("sensor", [None])[0]
            body = rows_to_json(fetch_metrics(hours, sensor))
            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path in ("/", "/index.html"):
            path = os.path.join(os.path.dirname(__file__), "index.html")
            with open(path, encoding="utf-8") as f:
                template = f.read()
            try:
                table_rows = rows_to_html(fetch_metrics(48, None))
            except Exception as exc:
                table_rows = (
                    f"<tr><td colspan='7'>{html.escape(str(exc))}</td></tr>"
                )
            data = template.replace("<!--TABLE_ROWS-->", table_rows).encode()
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
