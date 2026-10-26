
-- 1. Shipment-level temperature summary

SELECT
    s.shipment_id,
    s.origin_city,psql -U postgres -h localhost -p 5432 -d cold_chain_db -f sql/03_shipment_analytics.sql
    s.destination_city,
    COUNT(e.event_id) AS total_readings,
    ROUND(AVG(e.temperature_c), 2) AS avg_temperature,
    MIN(e.temperature_c) AS min_temperature,
    MAX(e.temperature_c) AS max_temperature,

    COUNT(e.event_id) FILTER (
        WHERE e.temperature_c < 2
           OR e.temperature_c > 8
    ) AS excursion_count

FROM shipments s

LEFT JOIN sensor_events e
    ON s.shipment_id = e.shipment_id

GROUP BY
    s.shipment_id,
    s.origin_city,
    s.destination_city

ORDER BY excursion_count DESC, s.shipment_id;


-- 2. Calculate excursion percentage using a CTE

WITH shipment_summary AS (
    SELECT
        shipment_id,
        COUNT(*) AS total_readings,

        COUNT(*) FILTER (
            WHERE temperature_c < 2
               OR temperature_c > 8
        ) AS excursion_count

    FROM sensor_events
    GROUP BY shipment_id
)

SELECT
    shipment_id,
    total_readings,
    excursion_count,

    ROUND(
        100.0 * excursion_count / NULLIF(total_readings, 0),
        2
    ) AS excursion_percentage

FROM shipment_summary
ORDER BY excursion_percentage DESC;


-- 3. Rank shipments by excursion count

WITH shipment_summary AS (
    SELECT
        s.shipment_id,
        COUNT(e.event_id) FILTER (
            WHERE e.temperature_c < 2
               OR e.temperature_c > 8
        ) AS excursion_count

    FROM shipments s

    LEFT JOIN sensor_events e
        ON s.shipment_id = e.shipment_id

    GROUP BY s.shipment_id
)

SELECT
    shipment_id,
    excursion_count,

    DENSE_RANK() OVER (
        ORDER BY excursion_count DESC
    ) AS excursion_rank

FROM shipment_summary
ORDER BY excursion_rank, shipment_id;


-- 4. Classify shipments by excursion count

WITH shipment_summary AS (
    SELECT
        s.shipment_id,

        COUNT(e.event_id) FILTER (
            WHERE e.temperature_c < 2
               OR e.temperature_c > 8
        ) AS excursion_count

    FROM shipments s

    LEFT JOIN sensor_events e
        ON s.shipment_id = e.shipment_id

    GROUP BY s.shipment_id
)

SELECT
    shipment_id,
    excursion_count,

    CASE
        WHEN excursion_count >= 3 THEN 'HIGH_RISK'
        WHEN excursion_count >= 1 THEN 'REVIEW_REQUIRED'
        ELSE 'NO_EXCURSIONS_DETECTED'
    END AS monitoring_status

FROM shipment_summary
ORDER BY excursion_count DESC, shipment_id;
