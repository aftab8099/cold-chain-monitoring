
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.transformation.validate_data import validate_event


def make_valid_event():
    return {
        "event_id": "event-001",
        "shipment_id": "SHP001",
        "city": "Delhi",
        "temperature_c": 5.0,
        "humidity_pct": 50.0,
        "sensor_id": "SENSOR-SHP001",
        "recorded_at": "2026-10-27T10:00:00+05:30",
    }


def test_valid_event():
    event = make_valid_event()

    is_valid, errors = validate_event(event)

    assert is_valid is True
    assert errors == []


def test_missing_event_id():
    event = make_valid_event()
    del event["event_id"]

    is_valid, errors = validate_event(event)

    assert is_valid is False
    assert any("event_id" in error for error in errors)


def test_invalid_humidity():
    event = make_valid_event()
    event["humidity_pct"] = 120

    is_valid, errors = validate_event(event)

    assert is_valid is False
    assert any("humidity_pct" in error for error in errors)


def test_temperature_excursion_is_valid_data():
    event = make_valid_event()
    event["temperature_c"] = -4.5

    is_valid, errors = validate_event(event)

    assert is_valid is True
    assert errors == []


def test_invalid_timestamp():
    event = make_valid_event()
    event["recorded_at"] = "not-a-timestamp"

    is_valid, errors = validate_event(event)

    assert is_valid is False
    assert any("recorded_at" in error for error in errors)


def test_humidity_nan_is_rejected():
    event = make_valid_event()
    event["humidity_pct"] = float("nan")

    is_valid, errors = validate_event(event)

    assert is_valid is False
    assert any("finite number" in error for error in errors)
