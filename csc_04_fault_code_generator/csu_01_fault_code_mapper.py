# Maps (component_id, VoltageState) pairs to fault code strings
import json
import os
from typing import Dict, Optional, Tuple
from models.diagnosis_result import VoltageState
from models.fault_code import FaultCode, Severity

_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fault_code_db.json')

_COMPONENT_STATE_MAP: Dict[Tuple[str, str], str] = {
    ("BAT", "UNDER_VOLTAGE"): "BAT_UV_001",
    ("BAT", "OVER_VOLTAGE"):  "BAT_OV_001",
    ("ESC", "UNDER_VOLTAGE"): "ESC_UV_001",
    ("ESC", "OVER_VOLTAGE"):  "ESC_OV_001",
    ("FC",  "UNDER_VOLTAGE"): "FC_UV_001",
    ("FC",  "OVER_VOLTAGE"):  "FC_OV_001",
    ("GPS", "UNDER_VOLTAGE"): "GPS_UV_001",
    ("GPS", "OVER_VOLTAGE"):  "GPS_OV_001",
    ("TEL", "UNDER_VOLTAGE"): "TEL_UV_001",
    ("TEL", "OVER_VOLTAGE"):  "TEL_OV_001",
    ("BEC", "UNDER_VOLTAGE"): "BEC_UV_001",
    ("BEC", "OVER_VOLTAGE"):  "BEC_OV_001",
    ("CAM", "UNDER_VOLTAGE"): "Cam_UV_001",
    ("CAM", "OVER_VOLTAGE"):  "Cam_OV_001",
    ("MOT", "UNDER_VOLTAGE"): "PWR_UV_001",
    ("MOT", "OVER_VOLTAGE"):  "PWR_OV_001",
}

_SEV_MAP = {"LOW": Severity.LOW, "MEDIUM": Severity.MEDIUM,
            "HIGH": Severity.HIGH, "CRITICAL": Severity.CRITICAL}


class FaultCodeMapper:
    def __init__(self, path: str = _DATA_PATH):
        self._db: Dict[str, FaultCode] = {}
        self._load(path)

    def _load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data['fault_codes']:
            fc = FaultCode(
                code=item['code'],
                component_id=item['component_id'],
                fault_type=item['fault_type'],
                severity=_SEV_MAP[item['severity']],
                description_ko=item['description_ko'],
                maintenance_ko=item['maintenance_ko'],
            )
            self._db[fc.code] = fc

    def get_code(self, component_id: str, state: VoltageState) -> Optional[str]:
        key = (component_id, state.value)
        return _COMPONENT_STATE_MAP.get(key)

    def get_fault_code_obj(self, code: str) -> Optional[FaultCode]:
        return self._db.get(code)

    def get_all(self) -> Dict[str, FaultCode]:
        return dict(self._db)
