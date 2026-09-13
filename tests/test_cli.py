import json
import subprocess
import sys
from datetime import UTC, datetime

import pytest
from bleak.exc import BleakError

from govee_h5075.cli import (
    create_parser,
    display_reading,
    display_scan,
    display_timeout,
    execute,
    format_reading,
)
from govee_h5075.reading import Reading


def reading() -> Reading:
    return Reading(
        observed_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        address="AA:BB:CC:DD:EE:FF",
        name="GVH5075_EEFF",
        temperature_c=21.5,
        relative_humidity_percent=48.2,
        battery_percent=87,
        rssi_dbm=-55,
    )


def test_format_reading_as_text() -> None:
    assert format_reading(reading(), as_json=False) == (
        "2026-01-02T03:04:05+00:00 AA:BB:CC:DD:EE:FF "
        "GVH5075_EEFF 21.5°C 48.2% battery=87% rssi=-55dBm"
    )


def test_format_reading_as_json() -> None:
    assert json.loads(format_reading(reading(), as_json=True)) == reading().to_dict()


def test_format_reading_handles_missing_optional_data() -> None:
    incomplete = Reading(
        observed_at=reading().observed_at,
        address=reading().address,
        name=None,
        temperature_c=reading().temperature_c,
        relative_humidity_percent=reading().relative_humidity_percent,
        battery_percent=reading().battery_percent,
        rssi_dbm=None,
    )

    assert " - " in format_reading(incomplete, as_json=False)
    assert "rssi=unknown" in format_reading(incomplete, as_json=False)


@pytest.mark.parametrize(
    ("arguments", "command"),
    [
        (["scan"], "scan"),
        (["read"], "read"),
        (["monitor"], "monitor"),
    ],
)
def test_parser_accepts_each_command(arguments: list[str], command: str) -> None:
    assert create_parser().parse_args(arguments).command == command


def test_module_displays_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "govee_h5075", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "scan" in result.stdout
    assert "read" in result.stdout
    assert "monitor" in result.stdout
    assert result.stderr == ""


def test_execute_reports_bluetooth_errors(capsys) -> None:
    async def fail() -> int:
        raise BleakError("adapter unavailable")

    assert execute(fail()) == 1
    assert capsys.readouterr().err == "Bluetooth error: adapter unavailable\n"


def test_execute_returns_command_status() -> None:
    async def succeed() -> int:
        return 7

    assert execute(succeed()) == 7


def test_execute_handles_interrupt() -> None:
    async def interrupt() -> int:
        raise KeyboardInterrupt

    assert execute(interrupt()) == 130


def test_display_scan_prints_readings(capsys) -> None:
    assert display_scan([reading()], as_json=True) == 0
    assert json.loads(capsys.readouterr().out) == reading().to_dict()


def test_display_scan_reports_no_sensors(capsys) -> None:
    assert display_scan([], as_json=False) == 1
    assert capsys.readouterr().err == "No Govee H5075 sensors found\n"


def test_display_reading_prints_reading(capsys) -> None:
    assert display_reading(reading(), as_json=False) == 0
    assert "21.5°C" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("address", "message"),
    [
        (None, "No Govee H5075 reading received\n"),
        (
            "AA:BB:CC:DD:EE:FF",
            "No Govee H5075 reading received at AA:BB:CC:DD:EE:FF\n",
        ),
    ],
)
def test_display_timeout_reports_target(address: str | None, message: str, capsys) -> None:
    assert display_timeout(address) == 1
    assert capsys.readouterr().err == message
