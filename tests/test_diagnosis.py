# Unit tests for the diagnosis engine pipeline
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from models.diagnosis_result import VoltageState, Severity
from csc_01_component_db.csu_01_component_data_loader import ComponentDataLoader
from csc_03_diagnosis_engine.csu_01_voltage_comparator import VoltageComparator
from csc_03_diagnosis_engine.csu_02_state_classifier import StateClassifier
from csc_03_diagnosis_engine.csu_03_diagnosis_result_builder import DiagnosisResultBuilder
from csc_04_fault_code_generator.csu_01_fault_code_mapper import FaultCodeMapper
from csc_05_maintenance_support.csu_01_maintenance_action_mapper import MaintenanceActionMapper


class TestVoltageComparator(unittest.TestCase):
    def setUp(self):
        loader = ComponentDataLoader()
        loader.load()
        self._comps = {c.id: c for c in loader.get_all()}
        self._cmp = VoltageComparator()

    def _bat(self):
        return self._comps["BAT"]

    def test_battery_normal(self):
        state, zone = self._cmp.compare(self._bat(), 46.0)
        self.assertEqual(state, VoltageState.NORMAL)
        self.assertEqual(zone, "normal")

    def test_battery_warning_uv(self):
        state, zone = self._cmp.compare(self._bat(), 38.5)
        self.assertEqual(state, VoltageState.UNDER_VOLTAGE)
        self.assertEqual(zone, "warning")

    def test_battery_critical_uv(self):
        state, zone = self._cmp.compare(self._bat(), 37.0)
        self.assertEqual(state, VoltageState.UNDER_VOLTAGE)
        self.assertEqual(zone, "critical")

    def test_battery_critical_ov(self):
        state, zone = self._cmp.compare(self._bat(), 52.5)
        self.assertEqual(state, VoltageState.OVER_VOLTAGE)
        self.assertEqual(zone, "critical")

    def test_esc_no_ov_critical(self):
        esc = self._comps["ESC"]
        state, zone = self._cmp.compare(esc, 53.0)
        self.assertEqual(state, VoltageState.OVER_VOLTAGE)
        self.assertEqual(zone, "warning")  # no_ov_critical → warning

    def test_no_data_scenario(self):
        state, zone = self._cmp.compare(self._bat(), None, "NO_DATA")
        self.assertEqual(state, VoltageState.NO_DATA)

    def test_sensor_error_scenario(self):
        state, zone = self._cmp.compare(self._bat(), None, "SENSOR_ERROR")
        self.assertEqual(state, VoltageState.SENSOR_ERROR)

    def test_rapid_drop_scenario(self):
        state, zone = self._cmp.compare(self._bat(), 40.0, "RAPID_DROP")
        self.assertEqual(state, VoltageState.RAPID_DROP)

    def test_fc_ov_critical(self):
        fc = self._comps["FC"]
        state, zone = self._cmp.compare(fc, 5.6)
        self.assertEqual(state, VoltageState.OVER_VOLTAGE)
        self.assertEqual(zone, "critical")


class TestStateClassifier(unittest.TestCase):
    def setUp(self):
        self._clf = StateClassifier()

    def test_normal_is_low(self):
        self.assertEqual(self._clf.classify(VoltageState.NORMAL, "normal"), Severity.LOW)

    def test_uv_warning_is_high(self):
        self.assertEqual(self._clf.classify(VoltageState.UNDER_VOLTAGE, "warning"), Severity.HIGH)

    def test_uv_critical_is_critical(self):
        self.assertEqual(
            self._clf.classify(VoltageState.UNDER_VOLTAGE, "critical"), Severity.CRITICAL
        )

    def test_rapid_drop_is_critical(self):
        self.assertEqual(
            self._clf.classify(VoltageState.RAPID_DROP, "warning"), Severity.CRITICAL
        )


class TestFaultCodeMapper(unittest.TestCase):
    def setUp(self):
        self._mapper = FaultCodeMapper()

    def test_bat_uv(self):
        self.assertEqual(self._mapper.get_code("BAT", VoltageState.UNDER_VOLTAGE), "BAT_UV_001")

    def test_bat_ov(self):
        self.assertEqual(self._mapper.get_code("BAT", VoltageState.OVER_VOLTAGE), "BAT_OV_001")

    def test_bec_no_ov_code(self):
        self.assertIsNone(self._mapper.get_code("BEC", VoltageState.OVER_VOLTAGE))

    def test_mot_uv_is_pwr(self):
        self.assertEqual(self._mapper.get_code("MOT", VoltageState.UNDER_VOLTAGE), "PWR_UV_001")

    def test_cam_codes(self):
        self.assertEqual(self._mapper.get_code("CAM", VoltageState.UNDER_VOLTAGE), "Cam_UV_001")
        self.assertEqual(self._mapper.get_code("CAM", VoltageState.OVER_VOLTAGE), "Cam_OV_001")

    def test_normal_has_no_code(self):
        self.assertIsNone(self._mapper.get_code("BAT", VoltageState.NORMAL))


class TestMaintenanceMapper(unittest.TestCase):
    def setUp(self):
        self._mapper = MaintenanceActionMapper()

    def test_bat_uv_has_maintenance(self):
        text = self._mapper.get_action("BAT_UV_001")
        self.assertIn("착륙", text)

    def test_normal_state_message(self):
        text = self._mapper.get_action(None, VoltageState.NORMAL)
        self.assertIn("정상", text)

    def test_no_data_message(self):
        text = self._mapper.get_action(None, VoltageState.NO_DATA)
        self.assertIn("센서", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
