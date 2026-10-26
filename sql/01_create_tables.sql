
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    origin_city VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    dispatch_time TIMESTAMPTZ,
    expected_delivery_time TIMESTAMPTZ,
    shipment_status VARCHAR(30) NOT NULL DEFAULT 'IN_TRANSIT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_events (
    event_id UUID PRIMARY KEY,
    shipment_id VARCHAR(50) NOT NULL
        REFERENCES shipments(shipment_id),
    city VARCHAR(100) NOT NULL,
    temperature_c NUMERIC(6, 2) NOT NULL,
    humidity_pct NUMERIC(6, 2) NOT NULL
        CHECK (humidity_pct >= 0 AND humidity_pct <= 100),
    sensor_id VARCHAR(100) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quarantined_events (
    quarantine_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT,
    shipment_id TEXT,
    raw_record JSONB NOT NULL,
    error_messages JSONB NOT NULL,
    source_file TEXT,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    records_read INTEGER NOT NULL DEFAULT 0,
    records_loaded INTEGER NOT NULL DEFAULT 0,
    records_quarantined INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_sensor_events_shipment_time
    ON sensor_events (shipment_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_events_recorded_at
    ON sensor_events (recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_events_sensor_time
    ON sensor_events (sensor_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_quarantined_events_time
    ON quarantined_events (quarantined_at DESC);