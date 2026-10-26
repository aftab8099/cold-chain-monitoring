
import json
import math
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_FIELDS = [
    "event_id",
    "shipment_id",
    "city",
    "temperature_c",
    "humidity_pct",
    "sensor_id",
    "recorded_at",
]


def validate_event(event):
    """Return (is_valid, error_messages) for a sensor event."""
    errors = []

    if not isinstance(event, dict):
        return False, ["Record must be a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in event or event[field] is None:
            errors.append(f"Missing required field: {field}")
        elif isinstance(event[field], str) and not event[field].strip():
            errors.append(f"Empty required field: {field}")

    if errors:
        return False, errors

    # Validate numeric values and reject booleans, NaN and infinity.
    for field in ("temperature_c", "humidity_pct"):
        value = event[field]

        if isinstance(value, bool):
            errors.append(f"{field} must be numeric")
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            errors.append(f"{field} must be numeric")
            continue

        if not math.isfinite(numeric_value):
            errors.append(f"{field} must be a finite number")
            continue

        event[field] = numeric_value

    if "humidity_pct" not in errors_as_fields(errors):
        humidity = event["humidity_pct"]
        if isinstance(humidity, (int, float)) and not 0 <= humidity <= 100:
            errors.append("humidity_pct must be between 0 and 100")

    # Temperature excursions are valid observations, not invalid data.
    # The monitoring stage will flag temperatures outside 2°C–8°C.

    try:
        timestamp = datetime.fromisoformat(
            event["recorded_at"].replace("Z", "+00:00")
        )
        if timestamp.tzinfo is None:
            errors.append("recorded_at must include a timezone")
    except (ValueError, TypeError, AttributeError):
        errors.append("recorded_at must be a valid ISO 8601 timestamp")

    return len(errors) == 0, errors


def errors_as_fields(errors):
    """Return field names with numeric validation errors."""
    fields = set()

    for error in errors:
        for field in ("temperature_c", "humidity_pct"):
            if error.startswith(f"{field} "):
                fields.add(field)

    return fields


def main():
    raw_files = sorted(RAW_DIR.glob("sensor_events_*.json"))

    if not raw_files:
        print("No raw sensor files found. Run the data generator first.")
        return

    valid_records = []
    invalid_records = []

    for raw_file in raw_files:
        with raw_file.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            print(f"Skipping {raw_file.name}: expected a JSON array.")
            continue

        for event in records:
            is_valid, errors = validate_event(event)

            if is_valid:
                valid_records.append(event)
            else:
                invalid_records.append({
                    "record": event,
                    "errors": errors,
                    "source_file": raw_file.name,
                })

    output_file = PROCESSED_DIR / "validated_sensor_events.json"
    quarantine_file = QUARANTINE_DIR / "invalid_sensor_events.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(valid_records, file, indent=4)

    with quarantine_file.open("w", encoding="utf-8") as file:
        json.dump(invalid_records, file, indent=4)

    print("\nData validation completed!")
    print(f"Valid records: {len(valid_records)}")
    print(f"Invalid records: {len(invalid_records)}")
    print(f"Processed file: {output_file}")
    print(f"Quarantine file: {quarantine_file}")


if __name__ == "__main__":
    main()
