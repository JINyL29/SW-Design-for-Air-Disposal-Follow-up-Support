# Maps (VoltageState, zone) pairs to Severity enum values
from typing import Optional
from models.diagnosis_result import VoltageState, Severity

_SEVERITY_ORDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


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

    @staticmethod
    def resolve(zone_severity: Severity,
                code_severity: Optional[Severity],
                zone: str = "normal") -> Severity:
        """전압 zone 심각도와 부품별 심각도 중 더 높은 값을 반환.

        BAT/ESC/BEC 같이 fault_code_db에 CRITICAL로 지정된 부품은
        경고 구간(warning)이더라도 CRITICAL로 상향된다.
        """
        if code_severity is None:
            return zone_severity
        return _SEVERITY_ORDER[max(
            _SEVERITY_ORDER.index(zone_severity),
            _SEVERITY_ORDER.index(code_severity),
        )]
