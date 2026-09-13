import asyncio
from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from govee_h5075.reading import Reading
from govee_h5075.sensor import (
    ReadingBuffer,
    _matches_address,
    _read_from,
    _scan_from,
)


def reading(temperature_c: float) -> Reading:
    return Reading(
        observed_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        address="AA:BB:CC:DD:EE:FF",
        name="GVH5075_EEFF",
        temperature_c=temperature_c,
        relative_humidity_percent=48.2,
        battery_percent=87,
        rssi_dbm=-55,
    )


def test_reading_buffer_keeps_latest_reading() -> None:
    async def exercise() -> None:
        buffer = ReadingBuffer()
        buffer.add(reading(21.5))
        buffer.add(reading(21.6))

        assert await buffer.get() == reading(21.6)

    asyncio.run(exercise())


def test_reading_buffer_keeps_each_sensor() -> None:
    async def exercise() -> None:
        buffer = ReadingBuffer()
        second_sensor = replace(
            reading(19.0),
            address="11:22:33:44:55:66",
            name="GVH5075_5566",
        )

        buffer.add(reading(21.5))
        buffer.add(second_sensor)
        buffer.add(reading(21.6))

        assert await buffer.get() == reading(21.6)
        assert await asyncio.wait_for(buffer.get(), timeout=0.01) == second_sensor

    asyncio.run(exercise())


def test_address_matching_is_case_insensitive() -> None:
    assert _matches_address(reading(21.5), "aa:bb:cc:dd:ee:ff")
    assert _matches_address(reading(21.5), None)
    assert not _matches_address(reading(21.5), "11:22:33:44:55:66")


def test_read_from_returns_first_reading_and_closes_stream() -> None:
    closed = False

    async def stream() -> AsyncIterator[Reading]:
        nonlocal closed
        try:
            yield reading(21.5)
            yield reading(21.6)
        finally:
            closed = True

    assert asyncio.run(_read_from(stream(), timeout=1)) == reading(21.5)
    assert closed


def test_read_from_times_out_and_closes_stream() -> None:
    closed = False

    async def stream() -> AsyncIterator[Reading]:
        nonlocal closed
        try:
            await asyncio.Future()
            yield reading(21.5)
        finally:
            closed = True

    with pytest.raises(TimeoutError):
        asyncio.run(_read_from(stream(), timeout=0.01))
    assert closed


def test_scan_from_returns_first_reading_per_sensor() -> None:
    second_sensor = replace(
        reading(19.0),
        address="11:22:33:44:55:66",
        name="GVH5075_5566",
    )

    async def stream() -> AsyncIterator[Reading]:
        yield reading(21.5)
        yield reading(21.6)
        yield second_sensor
        await asyncio.Future()

    assert asyncio.run(_scan_from(stream(), timeout=0.01)) == [
        reading(21.5),
        second_sensor,
    ]
