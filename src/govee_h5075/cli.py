import argparse
import asyncio
import json
import sys
from collections.abc import Coroutine
from typing import Any

from bleak.exc import BleakError

from .reading import Reading
from .sensor import read, readings, scan


def format_reading(reading: Reading, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(reading.to_dict())

    name = reading.name or "-"
    rssi = f"{reading.rssi_dbm}dBm" if reading.rssi_dbm is not None else "unknown"
    return (
        f"{reading.observed_at.isoformat()} {reading.address} {name} "
        f"{reading.temperature_c:.1f}°C "
        f"{reading.relative_humidity_percent:.1f}% "
        f"battery={reading.battery_percent}% rssi={rssi}"
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="govee-h5075",
        description="Read Govee H5075 Bluetooth advertisements",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    scan_parser = commands.add_parser("scan", help="find nearby H5075 sensors")
    scan_parser.add_argument("--timeout", type=float, default=20)
    scan_parser.add_argument("--json", action="store_true")

    read_parser = commands.add_parser("read", help="read one advertisement")
    read_parser.add_argument("--address")
    read_parser.add_argument("--timeout", type=float, default=20)
    read_parser.add_argument("--json", action="store_true")

    monitor_parser = commands.add_parser("monitor", help="stream advertisements")
    monitor_parser.add_argument("--address")
    monitor_parser.add_argument("--json", action="store_true")

    return parser


def display_scan(found: list[Reading], *, as_json: bool) -> int:
    for reading in found:
        print(format_reading(reading, as_json=as_json), flush=True)
    if not found:
        print("No Govee H5075 sensors found", file=sys.stderr)
        return 1
    return 0


def display_reading(reading: Reading, *, as_json: bool) -> int:
    print(format_reading(reading, as_json=as_json), flush=True)
    return 0


def display_timeout(address: str | None) -> int:
    target = f" at {address}" if address else ""
    print(f"No Govee H5075 reading received{target}", file=sys.stderr)
    return 1


async def run(args: argparse.Namespace) -> int:
    if args.command == "scan":
        found = await scan(timeout=args.timeout)
        return display_scan(found, as_json=args.json)

    if args.command == "read":
        try:
            reading = await read(address=args.address, timeout=args.timeout)
        except TimeoutError:
            return display_timeout(args.address)
        return display_reading(reading, as_json=args.json)

    async for reading in readings(address=args.address):
        display_reading(reading, as_json=args.json)
    return 0


def execute(command: Coroutine[Any, Any, int]) -> int:
    try:
        return asyncio.run(command)
    except KeyboardInterrupt:
        return 130
    except BleakError as error:
        print(f"Bluetooth error: {error}", file=sys.stderr)
        return 1


def main() -> int:
    args = create_parser().parse_args()
    return execute(run(args))
