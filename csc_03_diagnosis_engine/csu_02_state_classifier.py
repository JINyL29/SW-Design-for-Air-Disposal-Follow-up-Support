# Maps (VoltageState, zone) pairs to Severity enum values
from models.diagnosis_result import VoltageState, Severity


class StateClassifier:
    _SEVERITY_MAP = {
        (VoltageState.NORMAL,        "normal"):   Severity.LOW,
        (VoltageState.UNDER_VOLTAGE, "warning"):  Severity.HIGH,
        (VoltageState.UNDER_VOLTAGE, "critical"): Severity.CRITICAL,
        (VoltageState.OVER_VOLTAGE,  "warning"):  Severity.HIGH,
        (VoltageState.OVER_VOLTAGE,  "critical"): Severity.CRITICAL,
        (VoltageState.NO_DATA,       "warning"):  Severity.HIGH,
        (VoltageState.SENSOR_ERROR,  "warning"):  Severity.HIGH,
        (VoltageState.RAPID_DROP,    "warning"):  Severity.CRITICAL,
    }

    def classify(self, state: VoltageState, zone: str) -> Severity:
        return self._SEVERITY_MAP.get((state, zone), Severity.MEDIUM)
