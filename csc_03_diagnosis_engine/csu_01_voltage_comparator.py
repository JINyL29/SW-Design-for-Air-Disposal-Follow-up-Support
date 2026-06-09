# Compares measured voltage against component thresholds and returns state + severity zone
from typing import Optional, Tuple
from models.component import Component
from models.diagnosis_result import VoltageState


class VoltageComparator:
    def compare(
        self,
        component: Component,
        voltage: Optional[float],
        scenario: Optional[str] = None,
    ) -> Tuple[VoltageState, str]:
        """Returns (VoltageState, zone) where zone is 'critical'/'warning'/'normal'."""

        if scenario == "SENSOR_ERROR":
            return VoltageState.SENSOR_ERROR, "warning"

        if scenario == "NO_DATA" or voltage is None:
            return VoltageState.NO_DATA, "warning"

        if scenario == "RAPID_DROP":
            return VoltageState.RAPID_DROP, "warning"

        crit_low = component.voltage_min        # below this = CRITICAL UV
        normal_min = component.voltage_warn_high  # [crit_low, normal_min) = WARNING UV
        normal_max = component.voltage_max        # above this = OV

        if voltage < crit_low:
            return VoltageState.UNDER_VOLTAGE, "critical"

        if voltage < normal_min:
            return VoltageState.UNDER_VOLTAGE, "warning"

        if voltage <= normal_max:
            return VoltageState.NORMAL, "normal"

        # Over-voltage
        if component.has_ov_critical:
            return VoltageState.OVER_VOLTAGE, "critical"
        return VoltageState.OVER_VOLTAGE, "warning"
