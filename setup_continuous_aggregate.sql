-- Global Hack Week: Accelerate Dashboards with Continuous Aggregates
-- Tiger Cloud service: stillbench (hypertable from tiger-hypertable)
-- https://www.mlh.com/events/global-hack-week-open-source-90/challenges/01a11b5a-2e18-6061-22b7-5bd8eecbc563

CREATE MATERIALIZED VIEW IF NOT EXISTS ghw_sensor_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket(INTERVAL '1 hour', time) AS bucket,
    sensor_id,
    metric,
    COUNT(*)::BIGINT AS sample_count,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value
FROM ghw_sensor_readings
GROUP BY bucket, sensor_id, metric
WITH NO DATA;

ALTER MATERIALIZED VIEW ghw_sensor_hourly SET (timescaledb.materialized_only = false);

SELECT add_continuous_aggregate_policy(
    'ghw_sensor_hourly',
    start_offset => NULL,
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_ghw_sensor_hourly_sensor_bucket
    ON ghw_sensor_hourly (sensor_id, metric, bucket DESC);

-- Initial refresh (run outside a multi-statement transaction):
--   tiger db query stillbench -c "CALL refresh_continuous_aggregate('ghw_sensor_hourly', NULL, NULL);"
