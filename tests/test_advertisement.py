from datetime import UTC, datetime

import pytest

from govee_h5075.advertisement import (
    H5075Advertisements,
    H5075_MANUFACTURER_ID,
    decode,
    reading_from_advertisement,
)

SAMPLE_PAYLOAD = b"\x00" + (215482).to_bytes(3, byteorder="big") + b"\x57\x00"


def test_decode_payload() -> None:
    values = decode(SAMPLE_PAYLOAD)

    assert values.temperature_c == 21.5
    assert values.relative_humidity_percent == 48.2
    assert values.battery_percent == 87


def test_decode_negative_temperature() -> None:
    values = decode(bytes.fromhex("00 80 d4 b8 5a 00"))

    assert values.temperature_c == -5.4
    assert values.relative_humidity_percent == 45.6
    assert values.battery_percent == 90


def test_decode_valid_boundaries() -> None:
    payload = b"\x00" + (600999).to_bytes(3, byteorder="big") + b"\x64"

    values = decode(payload)

    assert values.temperature_c == 60
    assert values.relative_humidity_percent == 99.9


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"\x00\x01\x02\x03", "at least 5 bytes"),
        (bytes.fromhex("00 00 52 08 65"), "battery percentage"),
        (b"\x00" + (601000).to_bytes(3, byteorder="big") + b"\x64", "temperature"),
    ],
)
def test_decode_rejects_invalid_payload(payload: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        decode(payload)


def test_reading_from_advertisement_adds_transport_data() -> None:
    observed_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

    reading = reading_from_advertisement(
        address="AA:BB:CC:DD:EE:FF",
        name="GVH5075_EEFF",
        manufacturer_data={H5075_MANUFACTURER_ID: SAMPLE_PAYLOAD},
        rssi_dbm=-55,
        observed_at=observed_at,
    )

    assert reading is not None
    assert reading.observed_at == observed_at
    assert reading.address == "AA:BB:CC:DD:EE:FF"
    assert reading.name == "GVH5075_EEFF"
    assert reading.temperature_c == 21.5
    assert reading.relative_humidity_percent == 48.2
    assert reading.battery_percent == 87
    assert reading.rssi_dbm == -55


def test_advertisements_remember_name_when_data_arrives_separately() -> None:
    advertisements = H5075Advertisements()

    assert advertisements.reading(
        address="AA:BB:CC:DD:EE:FF",
        name="GVH5075_EEFF",
        manufacturer_data={},
        rssi_dbm=-55,
    ) is None

    reading = advertisements.reading(
        address="AA:BB:CC:DD:EE:FF",
        name=None,
        manufacturer_data={H5075_MANUFACTURER_ID: SAMPLE_PAYLOAD},
        rssi_dbm=-56,
    )

    assert reading is not None
    assert reading.name == "GVH5075_EEFF"
    assert reading.rssi_dbm == -56


@pytest.mark.parametrize(
    ("name", "manufacturer_data"),
    [
        ("GVH5074_EEFF", {H5075_MANUFACTURER_ID: SAMPLE_PAYLOAD}),
        ("GVH5075_EEFF", {}),
        (None, {H5075_MANUFACTURER_ID: SAMPLE_PAYLOAD}),
    ],
)
def test_reading_from_advertisement_ignores_other_devices(
    name: str | None,
    manufacturer_data: dict[int, bytes],
) -> None:
    assert reading_from_advertisement(
        address="AA:BB:CC:DD:EE:FF",
        name=name,
        manufacturer_data=manufacturer_data,
        rssi_dbm=-62,
    ) is None
