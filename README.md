# govee-h5075-reader

A Python library and CLI for reading temperature, humidity, and battery data
from Govee H5075 Bluetooth sensors.

The reader listens for Bluetooth Low Energy advertisements. It does not pair
with or maintain a connection to the sensor.

## Requirements

- Python 3.11 or later
- Linux with BlueZ
- A Bluetooth Low Energy adapter supported by [Bleak](https://bleak.readthedocs.io/)

On Debian, install Python virtual environment support before creating an
environment:

```bash
sudo apt-get install python3-venv
```

Install the package from GitHub:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install \
  git+https://github.com/ashr0/govee-h5075-reader.git
```

## CLI

Find nearby H5075 sensors:

```bash
govee-h5075 scan
```

Read one advertisement from a sensor:

```bash
govee-h5075 read --address AA:BB:CC:DD:EE:FF
```

Print the reading as JSON:

```bash
govee-h5075 read --address AA:BB:CC:DD:EE:FF --json
```

Stream readings as JSON Lines until interrupted:

```bash
govee-h5075 monitor --address AA:BB:CC:DD:EE:FF --json
```

Example JSON output:

```json
{"observed_at":"2026-01-02T03:04:05+00:00","address":"AA:BB:CC:DD:EE:FF","name":"GVH5075_EEFF","temperature_c":21.5,"relative_humidity_percent":48.2,"battery_percent":87,"rssi_dbm":-55}
```

The address and reading above are fictional.

## Python API

Read one advertisement:

```python
import asyncio

from govee_h5075 import read


async def main() -> None:
    reading = await read(address="AA:BB:CC:DD:EE:FF", timeout=20)
    print(reading.temperature_c)
    print(reading.relative_humidity_percent)


asyncio.run(main())
```

Consume a continuous stream:

```python
from govee_h5075 import readings


async for reading in readings(address="AA:BB:CC:DD:EE:FF"):
    print(reading.to_dict())
```

## Development

Run the unit tests:

```bash
uv run --extra test pytest
```

Run the optional integration test with a nearby sensor:

```bash
H5075_TEST_ADDRESS=AA:BB:CC:DD:EE:FF \
  uv run --extra test pytest tests/integration
```

## Attribution

The H5075 advertisement decoding is based on
[govee-h5075-thermo-hygrometer](https://github.com/Heckie75/govee-h5075-thermo-hygrometer),
Copyright (c) 2023 Heckie, used under the MIT License.
