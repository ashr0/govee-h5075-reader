import asyncio
import os

import pytest

from govee_h5075 import read


def test_reads_a_live_h5075() -> None:
    address = os.environ.get("H5075_TEST_ADDRESS")
    if address is None:
        pytest.skip("H5075_TEST_ADDRESS is not set")

    reading = asyncio.run(read(address=address, timeout=30))

    assert reading.address == address.upper()
    assert -20 <= reading.temperature_c <= 60
    assert 0 <= reading.relative_humidity_percent <= 99.9
    assert 0 <= reading.battery_percent <= 100
