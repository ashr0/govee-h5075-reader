from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from govee_h5075.reading import Reading, SensorValues


def test_reading_serializes_for_external_consumers() -> None:
    reading = Reading(
        observed_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        address="AA:BB:CC:DD:EE:FF",
        name="GVH5075_EEFF",
        temperature_c=21.5,
        relative_humidity_percent=48.2,
        battery_percent=87,
        rssi_dbm=-55,
    )

    assert reading.to_dict() == {
        "observed_at": "2026-01-02T03:04:05+00:00",
        "address": "AA:BB:CC:DD:EE:FF",
        "name": "GVH5075_EEFF",
        "temperature_c": 21.5,
        "relative_humidity_percent": 48.2,
        "battery_percent": 87,
        "rssi_dbm": -55,
    }


def test_sensor_values_are_immutable() -> None:
    values = SensorValues(21.5, 48.2, 87)

    with pytest.raises(FrozenInstanceError):
        values.temperature_c = 21.6
