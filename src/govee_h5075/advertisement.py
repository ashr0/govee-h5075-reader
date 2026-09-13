from collections.abc import Mapping
from datetime import UTC, datetime

from .reading import Reading, SensorValues


H5075_MANUFACTURER_ID = 0xEC88
H5075_NAME_PREFIX = "GVH5075_"


class H5075Advertisements:
    def __init__(self) -> None:
        self._names: dict[str, str] = {}

    def reading(
        self,
        *,
        address: str,
        name: str | None,
        manufacturer_data: Mapping[int, bytes],
        rssi_dbm: int | None,
        observed_at: datetime | None = None,
    ) -> Reading | None:
        normalized_address = address.upper()
        if name is not None and name.startswith(H5075_NAME_PREFIX):
            self._names[normalized_address] = name

        return reading_from_advertisement(
            address=normalized_address,
            name=self._names.get(normalized_address),
            manufacturer_data=manufacturer_data,
            rssi_dbm=rssi_dbm,
            observed_at=observed_at,
        )


def decode(payload: bytes) -> SensorValues:
    if len(payload) < 5:
        raise ValueError("H5075 manufacturer data must contain at least 5 bytes")

    encoded_values = int.from_bytes(payload[1:4], byteorder="big")
    is_negative = bool(encoded_values & 0x800000)
    magnitude = encoded_values & 0x7FFFFF

    temperature_c = (magnitude // 1000) / 10
    if is_negative:
        temperature_c = -temperature_c

    relative_humidity_percent = (magnitude % 1000) / 10
    battery_percent = payload[4]

    if not -20 <= temperature_c <= 60:
        raise ValueError(f"invalid temperature: {temperature_c} °C")
    if not 0 <= battery_percent <= 100:
        raise ValueError(f"invalid battery percentage: {battery_percent}%")

    return SensorValues(
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        battery_percent=battery_percent,
    )


def reading_from_advertisement(
    *,
    address: str,
    name: str | None,
    manufacturer_data: Mapping[int, bytes],
    rssi_dbm: int | None,
    observed_at: datetime | None = None,
) -> Reading | None:
    payload = manufacturer_data.get(H5075_MANUFACTURER_ID)
    if name is None or not name.startswith(H5075_NAME_PREFIX) or payload is None:
        return None

    values = decode(payload)
    return Reading(
        observed_at=observed_at or datetime.now(UTC),
        address=address.upper(),
        name=name,
        temperature_c=values.temperature_c,
        relative_humidity_percent=values.relative_humidity_percent,
        battery_percent=values.battery_percent,
        rssi_dbm=rssi_dbm,
    )
