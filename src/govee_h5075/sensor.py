import asyncio
from collections.abc import AsyncIterator

from bleak import AdvertisementData, BLEDevice, BleakScanner

from .advertisement import H5075Advertisements
from .reading import Reading


class ReadingBuffer:
    def __init__(self) -> None:
        self._addresses: asyncio.Queue[str] = asyncio.Queue()
        self._readings: dict[str, Reading] = {}

    def add(self, reading: Reading) -> None:
        if reading.address not in self._readings:
            self._addresses.put_nowait(reading.address)
        self._readings[reading.address] = reading

    async def get(self) -> Reading:
        address = await self._addresses.get()
        return self._readings.pop(address)


def _matches_address(reading: Reading, address: str | None) -> bool:
    return address is None or reading.address == address.upper()


async def readings(address: str | None = None) -> AsyncIterator[Reading]:
    buffer = ReadingBuffer()
    advertisements = H5075Advertisements()

    def receive(device: BLEDevice, advertisement: AdvertisementData) -> None:
        try:
            reading = advertisements.reading(
                address=device.address,
                name=advertisement.local_name or device.name,
                manufacturer_data=advertisement.manufacturer_data,
                rssi_dbm=advertisement.rssi,
            )
        except ValueError:
            return

        if reading is not None and _matches_address(reading, address):
            buffer.add(reading)

    async with BleakScanner(receive):
        while True:
            yield await buffer.get()


async def read(address: str | None = None, timeout: float = 20) -> Reading:
    return await _read_from(readings(address), timeout)


async def _read_from(stream: AsyncIterator[Reading], timeout: float) -> Reading:
    try:
        async with asyncio.timeout(timeout):
            return await anext(stream)
    finally:
        await stream.aclose()


async def scan(timeout: float = 20) -> list[Reading]:
    return await _scan_from(readings(), timeout)


async def _scan_from(
    stream: AsyncIterator[Reading], timeout: float
) -> list[Reading]:
    found: dict[str, Reading] = {}
    try:
        async with asyncio.timeout(timeout):
            async for reading in stream:
                found.setdefault(reading.address, reading)
    except TimeoutError:
        pass
    finally:
        await stream.aclose()

    return list(found.values())
