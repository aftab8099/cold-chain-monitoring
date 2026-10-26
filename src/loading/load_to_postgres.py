
import json
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

INPUT_FILE = PROCESSED_DIR / "validated_sensor_events.json"
QUARANTINE_FILE = QUARANTINE_DIR / "invalid_sensor_events.json"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "cold_chain_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}


def read_json_file(file_path):
    """Read a JSON file and return its contents."""
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_sensor_events(connection, records):
    """Insert validated sensor events without duplicating existing events."""
    if not records:
        return 0

    query = """
        INSERT INTO sensor_events (
            event_id,
            shipment_id,
            city,
            temperature_c,
            humidity_pct,
            sensor_id,
            recorded_at
        )
        VALUES %s
        ON CONFLICT (event_id) DO NOTHING;
    """

    values = [
        (
            record["event_id"],
            record["shipment_id"],
            record["city"],
            record["temperature_c"],
            record["humidity_pct"],
            record["sensor_id"],
            record["recorded_at"],
        )
        for record in records
    ]

    with connection.cursor() as cursor:
        execute_values(cursor, query, values, page_size=500)
        return cursor.rowcount


def count_quarantined_records():
    """Count invalid records from the quarantine JSON file."""
    if not QUARANTINE_FILE.exists():
        return 0

    quarantined_records = read_json_file(QUARANTINE_FILE)

    if not isinstance(quarantined_records, list):
        raise ValueError("Quarantine file must contain a JSON array.")

    return len(quarantined_records)


def start_pipeline_run(connection):
    """Create and commit a pipeline run before processing records."""
    query = """
        INSERT INTO pipeline_runs (
            status,
            records_read,
            records_loaded,
            records_quarantined
        )
        VALUES ('RUNNING', 0, 0, 0)
        RETURNING run_id;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        run_id = cursor.fetchone()[0]

    connection.commit()
    return run_id


def finish_pipeline_run(
    connection,
    run_id,
    status,
    records_read,
    records_loaded,
    records_quarantined,
    error_message=None,
):
    """Save the final status and metrics for a pipeline run."""
    query = """
        UPDATE pipeline_runs
        SET finished_at = CURRENT_TIMESTAMP,
            status = %s,
            records_read = %s,
            records_loaded = %s,
            records_quarantined = %s,
            error_message = %s
        WHERE run_id = %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                status,
                records_read,
                records_loaded,
                records_quarantined,
                error_message,
                run_id,
            ),
        )


def main():
    if not DB_CONFIG["password"]:
        print("ERROR: DB_PASSWORD is missing from your .env file.")
        sys.exit(1)

    run_id = None
    records_read = 0
    records_loaded = 0
    records_quarantined = 0

    try:
        # Create a run record that remains available if processing fails.
        with psycopg2.connect(**DB_CONFIG) as connection:
            run_id = start_pipeline_run(connection)

        print(f"Pipeline run started. Run ID: {run_id}")

        # Read and validate the expected JSON structure.
        if not INPUT_FILE.exists():
            raise FileNotFoundError(
                "Validated data file not found. "
                "Run the generator and validator first."
            )

        records = read_json_file(INPUT_FILE)

        if not isinstance(records, list):
            raise ValueError(
                "Expected a JSON array in the validated data file."
            )

        records_read = len(records)
        records_quarantined = count_quarantined_records()

        # Load records and mark the run successful in one transaction.
        with psycopg2.connect(**DB_CONFIG) as connection:
            records_loaded = load_sensor_events(connection, records)

            finish_pipeline_run(
                connection=connection,
                run_id=run_id,
                status="SUCCESS",
                records_read=records_read,
                records_loaded=records_loaded,
                records_quarantined=records_quarantined,
            )

        print("\nPipeline execution completed successfully!")
        print(f"Pipeline run ID: {run_id}")
        print(f"Validated records read: {records_read}")
        print(f"New records inserted: {records_loaded}")
        print(f"Duplicate records skipped: {records_read - records_loaded}")
        print(f"Quarantined records: {records_quarantined}")
        print("Pipeline status: SUCCESS")

    except Exception as error:
        error_message = str(error)[:2000]

        # A separate connection allows failure details to be saved even
        # when the loading transaction has rolled back.
        if run_id is not None:
            try:
                with psycopg2.connect(**DB_CONFIG) as connection:
                    finish_pipeline_run(
                        connection=connection,
                        run_id=run_id,
                        status="FAILED",
                        records_read=records_read,
                        records_loaded=records_loaded,
                        records_quarantined=records_quarantined,
                        error_message=error_message,
                    )
            except Exception as tracking_error:
                print(
                    "WARNING: Could not update the failed pipeline run: "
                    f"{tracking_error}"
                )

        print(f"\nPipeline failed: {error_message}")

        if run_id is not None:
            print(f"Pipeline run ID: {run_id}")

        sys.exit(1)


if __name__ == "__main__":
    main()
