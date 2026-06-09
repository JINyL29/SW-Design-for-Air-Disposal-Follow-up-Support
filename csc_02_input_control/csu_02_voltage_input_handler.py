# Validates and normalizes raw voltage input from the operator UI
from typing import Optional, Tuple
from models.component import Component


class VoltageInputHandler:
    SENSOR_ERROR_SENTINEL = -999.0  # sentinel value representing sensor error

    def validate(self, raw_value: str, component: Component) -> Tuple[bool, Optional[float], str]:
        """Returns (is_valid, voltage, error_message)."""
        if not raw_value.strip():
            return False, None, "전압값을 입력하세요."
        try:
            voltage = float(raw_value.strip())
        except ValueError:
            return False, None, "숫자 형식으로 입력하세요."
        if voltage < 0:
            return False, None, "음수 전압은 허용되지 않습니다. Sensor Error 시나리오를 사용하세요."
        if voltage > 1000:
            return False, None, "전압값이 너무 큽니다 (최대 1000V)."
        return True, voltage, ""

    def parse(self, raw_value: str) -> Optional[float]:
        try:
            v = float(raw_value.strip())
            return v if v >= 0 else None
        except (ValueError, AttributeError):
            return None

    def compute_deviation_pct(self, voltage: float, component: Component) -> float:
        """Percentage deviation from the nearest normal boundary."""
        normal_min = component.voltage_warn_high
        normal_max = component.voltage_max
        if voltage < normal_min:
            return -abs((normal_min - voltage) / normal_min * 100)
        elif voltage > normal_max:
            return abs((voltage - normal_max) / normal_max * 100)
        return 0.0

    def compute_gauge_pct(self, voltage: float, component: Component) -> float:
        """Returns 0.0-1.0 position within the display range [critical_low, normal_max*1.1]."""
        low = component.voltage_min
        high = component.voltage_max * 1.1
        if high <= low:
            return 0.5
        return max(0.0, min(1.0, (voltage - low) / (high - low)))
