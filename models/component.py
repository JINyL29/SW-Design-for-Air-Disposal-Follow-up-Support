# Component data model representing a drone electrical component with voltage thresholds
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Component:
    id: str
    name: str
    model_name: str
    voltage_min: float        # critical low threshold (below = CRITICAL UV)
    voltage_max: float        # normal max / rated max
    voltage_warn_low: float   # lower boundary of warning zone (== voltage_min)
    voltage_warn_high: float  # upper boundary of warning zone = normal_min
    priority: int
    has_ov_critical: bool = False  # True if voltage > voltage_max triggers CRITICAL OV

    @property
    def rated_range_str(self) -> str:
        return f"{self.voltage_warn_high:.2f} ~ {self.voltage_max:.2f}V"

    @property
    def warn_range_str(self) -> str:
        return f"{self.voltage_min:.2f} ~ {self.voltage_warn_high - 0.01:.2f}V"
