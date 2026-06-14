# DiagnosisResult model and associated enums for voltage state and severity classification
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class VoltageState(Enum):
    NORMAL = "NORMAL"
    UNDER_VOLTAGE = "UNDER_VOLTAGE"
    OVER_VOLTAGE = "OVER_VOLTAGE"
    NO_DATA = "NO_DATA"
    SENSOR_ERROR = "SENSOR_ERROR"
    RAPID_DROP = "RAPID_DROP"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DiagnosisResult:
    component_id: str
    state: VoltageState
    current_voltage: Optional[float]
    fault_code: Optional[str]
    severity: Severity
    maintenance_action: str
    diagnosed_at: datetime

    @property
    def is_fault(self) -> bool:
        return self.state != VoltageState.NORMAL

    @property
    def deviation_pct(self) -> Optional[float]:
        """Returns deviation percentage from normal range midpoint, or None."""
        return None  # Populated externally if needed
