# Tiger Dash

Hourly dashboard metrics backed by a **TimescaleDB continuous aggregate** on the `ghw_sensor_readings` hypertable from [tiger-hypertable](https://github.com/smriad/tiger-hypertable) (Tiger Cloud service **stillbench**).

Built for MLH Global Hack Week: [Accelerate Dashboards with Continuous Aggregates](https://www.mlh.com/events/global-hack-week-open-source-90/challenges/01a11b5a-2e18-6061-22b7-5bd8eecbc563).

## Apply the continuous aggregate

```bash
tiger db query stillbench --file setup_continuous_aggregate.sql
tiger db query stillbench -c "CALL refresh_continuous_aggregate('ghw_sensor_hourly', NULL, NULL);"
tiger db query stillbench --file verify_cagg.sql
```

The view `ghw_sensor_hourly` rolls up readings into **1-hour buckets** with `avg` / `min` / `max`, enables **real-time aggregation** (`materialized_only = false`), and refreshes every **5 minutes**.

## Run the dashboard locally

```bash
export DATABASE_URL="$(tiger db uri stillbench --with-password)"
pip install -r requirements.txt
python dashboard/server.py
```

Open http://localhost:8765 — the UI calls `/api/metrics`, which queries the continuous aggregate (not the raw hypertable).

## References

- [Continuous aggregates](https://docs.tigerdata.com/use-timescale/latest/continuous-aggregates/)
- [Time bucketing](https://docs.tigerdata.com/use-timescale/latest/time-buckets/)
