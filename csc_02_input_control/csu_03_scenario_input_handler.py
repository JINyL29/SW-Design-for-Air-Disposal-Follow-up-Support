# Maps fault-injection scenario names to representative voltage values
from typing import Optional
from models.component import Component


SCENARIO_LABELS = {
    "NORMAL":       "Normal",
    "UNDER_VOLTAGE": "Under-volt",
    "OVER_VOLTAGE":  "Over-volt",
    "NO_DATA":       "No Data",
    "SENSOR_ERROR":  "Sensor Error",
    "RAPID_DROP":    "Rapid Drop",
}


class ScenarioInputHandler:
    def get_voltage(self, scenario: str, component: Component) -> Optional[float]:
        """Returns a representative voltage for the scenario, or None for non-voltage scenarios."""
        normal_mid = (component.voltage_warn_high + component.voltage_max) / 2.0

        if scenario == "NORMAL":
            return round(normal_mid, 2)
        elif scenario == "UNDER_VOLTAGE":
            # 1V below the critical low threshold
            return round(component.voltage_min - 1.0, 2)
        elif scenario == "OVER_VOLTAGE":
            return round(component.voltage_max + 1.0, 2)
        elif scenario == "NO_DATA":
            return None
        elif scenario == "SENSOR_ERROR":
            return None  # No voltage — handled specially by diagnosis engine
        elif scenario == "RAPID_DROP":
            # Just below critical threshold (simulates sudden drop)
            return round(component.voltage_min - 0.5, 2)
        return None

    def is_no_voltage_scenario(self, scenario: str) -> bool:
        return scenario in ("NO_DATA", "SENSOR_ERROR")

    def get_all_scenarios(self):
        return list(SCENARIO_LABELS.keys())

    def label(self, scenario: str) -> str:
        return SCENARIO_LABELS.get(scenario, scenario)
