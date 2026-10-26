
import os
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "cold_chain_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

MIN_TEMP = 2.0
MAX_TEMP = 8.0

st.set_page_config(
    page_title="Cold Chain Monitoring",
    page_icon="🌡️",
    layout="wide",
)

st.title("Cold Chain Monitoring Dashboard")
st.caption("Shipment temperature monitoring and data quality analytics")

if not DB_CONFIG["password"]:
    st.error("DB_PASSWORD is missing from your .env file.")
    st.stop()


@st.cache_data(ttl=30)
def load_data():
    with psycopg2.connect(**DB_CONFIG) as connection:
        sensor_query = """
            SELECT
                event_id,
                shipment_id,
                city,
                temperature_c,
                humidity_pct,
                sensor_id,
                recorded_at
            FROM sensor_events
            ORDER BY recorded_at;
        """

        shipment_query = """
            SELECT
                s.shipment_id,
                s.origin_city,
                s.destination_city,
                COUNT(e.event_id) AS total_readings,

                ROUND(AVG(e.temperature_c), 2) AS avg_temperature,

                COUNT(e.event_id) FILTER (
                    WHERE e.temperature_c < %s
                       OR e.temperature_c > %s
                ) AS excursion_count

            FROM shipments s

            LEFT JOIN sensor_events e
                ON s.shipment_id = e.shipment_id

            GROUP BY
                s.shipment_id,
                s.origin_city,
                s.destination_city

            ORDER BY excursion_count DESC, s.shipment_id;
        """

        sensors = pd.read_sql_query(sensor_query, connection)

        shipments = pd.read_sql_query(
            shipment_query,
            connection,
            params=(MIN_TEMP, MAX_TEMP),
        )

    return sensors, shipments


try:
    sensors, shipments = load_data()
except Exception as error:
    st.error(f"Unable to load database data: {error}")
    st.stop()

if sensors.empty:
    st.warning("No sensor events found. Run the data generator and loader first.")
    st.stop()

sensors["recorded_at"] = pd.to_datetime(sensors["recorded_at"])

sensors["temperature_status"] = sensors["temperature_c"].apply(
    lambda temp: (
        "LOW"
        if temp < MIN_TEMP
        else "HIGH"
        if temp > MAX_TEMP
        else "NORMAL"
    )
)

excursions = sensors[
    (sensors["temperature_c"] < MIN_TEMP)
    | (sensors["temperature_c"] > MAX_TEMP)
]

total_events = len(sensors)
excursion_count = len(excursions)
average_temperature = sensors["temperature_c"].mean()
affected_shipments = excursions["shipment_id"].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Sensor Events", total_events)
col2.metric("Temperature Excursions", excursion_count)
col3.metric("Average Temperature", f"{average_temperature:.2f} °C")
col4.metric("Affected Shipments", affected_shipments)

st.divider()

st.subheader("Temperature Readings Over Time")

chart_data = sensors.set_index("recorded_at")

st.line_chart(
    chart_data[["temperature_c"]],
    y="temperature_c",
)

st.caption(
    f"Assumed acceptable temperature range: "
    f"{MIN_TEMP:.0f}°C to {MAX_TEMP:.0f}°C. "
    "The line chart shows observed readings; use the table below to identify excursions."
)

st.subheader("Shipment Risk Summary")

if not shipments.empty:
    shipments["monitoring_status"] = shipments["excursion_count"].apply(
        lambda count: (
            "HIGH_RISK"
            if count >= 3
            else "REVIEW_REQUIRED"
            if count >= 1
            else "NO_EXCURSIONS_DETECTED"
        )
    )

    st.dataframe(shipments, use_container_width=True)

st.subheader("Temperature Excursion Events")

if excursions.empty:
    st.success("No temperature excursions detected.")
else:
    st.warning(f"{excursion_count} temperature excursion event(s) detected.")
    st.dataframe(
        excursions.sort_values("recorded_at", ascending=False),
        use_container_width=True,
    )

st.subheader("All Sensor Readings")

st.dataframe(
    sensors.sort_values("recorded_at", ascending=False),
    use_container_width=True,
)

if st.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()
