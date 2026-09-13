from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class SensorValues:
    temperature_c: float
    relative_humidity_percent: float
    battery_percent: int


@dataclass(frozen=True)
class Reading:
    observed_at: datetime
    address: str
    name: str | None
    temperature_c: float
    relative_humidity_percent: float
    battery_percent: int
    rssi_dbm: int | None

    def to_dict(self) -> dict[str, str | float | int | None]:
        values = asdict(self)
        values["observed_at"] = self.observed_at.isoformat()
        return values
