
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

SHIPMENTS = [
    {"shipment_id": "SHP001", "city": "Delhi"},
    {"shipment_id": "SHP002", "city": "Mumbai"},
    {"shipment_id": "SHP003", "city": "Bengaluru"},
    {"shipment_id": "SHP004", "city": "Hyderabad"},
    {"shipment_id": "SHP005", "city": "Chennai"},
]


def generate_sensor_event(shipment):
    # Simulate normal temperatures and occasional temperature excursions.
    temperature = round(random.uniform(2, 8), 2)

    # Occasionally simulate an unsafe temperature.
    if random.random() < 0.15:
        temperature = round(random.choice([
            random.uniform(-5, 1.9),
            random.uniform(8.1, 15)
        ]), 2)

    return {
        "event_id": str(uuid.uuid4()),
        "shipment_id": shipment["shipment_id"],
        "city": shipment["city"],
        "temperature_c": temperature,
        "humidity_pct": round(random.uniform(30, 80), 2),
        "sensor_id": f"SENSOR-{shipment['shipment_id']}",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    events = [
        generate_sensor_event(shipment)
        for shipment in SHIPMENTS
    ]

    filename = datetime.now(timezone.utc).strftime(
        "sensor_events_%Y%m%dT%H%M%SZ.json"
    )
    output_file = RAW_DIR / filename

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)

    print(f"Generated {len(events)} sensor events.")
    print(f"Raw data saved to: {output_file}")


if __name__ == "__main__":
    main()