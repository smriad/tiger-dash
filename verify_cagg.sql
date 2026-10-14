SELECT view_name, materialization_hypertable_name
FROM timescaledb_information.continuous_aggregates
WHERE view_name = 'ghw_sensor_hourly';

SELECT bucket, sensor_id, metric, sample_count, round(avg_value::numeric, 2) AS avg_value
FROM ghw_sensor_hourly
ORDER BY bucket DESC, sensor_id, metric
LIMIT 12;
