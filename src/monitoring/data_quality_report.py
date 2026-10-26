
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


def main():
    if not DB_CONFIG["password"]:
        raise RuntimeError("DB_PASSWORD is missing from the .env file.")

    query = """
        SELECT
            COUNT(*) AS total_events,
            COUNT(DISTINCT event_id) AS unique_events,
            COUNT(*) FILTER (
                WHERE temperature_c < 2 OR temperature_c > 8
            ) AS excursion_events,
            COUNT(*) FILTER (
                WHERE humidity_pct < 0 OR humidity_pct > 100
            ) AS invalid_humidity_events,
            COUNT(*) FILTER (
                WHERE recorded_at IS NULL
            ) AS missing_timestamps
        FROM sensor_events;
    """

    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

    total, unique, excursions, invalid_humidity, missing_timestamps = result

    print("\nDATA QUALITY REPORT")
    print("=" * 45)
    print(f"Total sensor events: {total}")
    print(f"Unique event IDs: {unique}")
    print(f"Temperature excursion events: {excursions}")
    print(f"Invalid humidity events: {invalid_humidity}")
    print(f"Missing timestamps: {missing_timestamps}")

    if total != unique:
        print("WARNING: Duplicate event IDs detected.")
    else:
        print("PASS: No duplicate event IDs detected.")

    if invalid_humidity == 0 and missing_timestamps == 0:
        print("PASS: Humidity and timestamp checks passed.")


if __name__ == "__main__":
    main()
