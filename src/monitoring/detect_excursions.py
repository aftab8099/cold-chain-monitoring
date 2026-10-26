
import os
from pathlib import Path

import psycopg2
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


def main():
    if not DB_CONFIG["password"]:
        raise RuntimeError("DB_PASSWORD is missing from the .env file.")

    query = """
        SELECT
            shipment_id,
            city,
            temperature_c,
            humidity_pct,
            recorded_at,
            CASE
                WHEN temperature_c < %s THEN 'LOW_TEMPERATURE'
                WHEN temperature_c > %s THEN 'HIGH_TEMPERATURE'
                ELSE 'NORMAL'
            END AS temperature_status
        FROM sensor_events
        WHERE temperature_c < %s
           OR temperature_c > %s
        ORDER BY recorded_at DESC;
    """

    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (MIN_TEMP, MAX_TEMP, MIN_TEMP, MAX_TEMP),
            )
            excursions = cursor.fetchall()

    print("\nTEMPERATURE EXCURSION REPORT")
    print("=" * 75)

    if not excursions:
        print("No temperature excursions detected.")
        return

    for row in excursions:
        shipment_id, city, temp, humidity, recorded_at, status = row

        print(f"Shipment: {shipment_id}")
        print(f"Location: {city}")
        print(f"Temperature: {temp} °C")
        print(f"Humidity: {humidity}%")
        print(f"Recorded at: {recorded_at}")
        print(f"Status: {status}")
        print("-" * 75)

    print(f"Total excursion events: {len(excursions)}")


if __name__ == "__main__":
    main()
