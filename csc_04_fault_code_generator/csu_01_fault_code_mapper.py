# Maps (component_id, VoltageState) pairs to fault code strings
import json
import os
from typing import Dict, Optional, Tuple
from models.diagnosis_result import VoltageState
from models.fault_code import FaultCode, Severity

_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fault_code_db.json')

_COMPONENT_STATE_MAP: Dict[Tuple[str, str], str] = {
    # BAT
    ("BAT", "UNDER_VOLTAGE"): "BAT_UV_001",
    ("BAT", "OVER_VOLTAGE"):  "BAT_OV_001",
    # ESC
    ("ESC", "UNDER_VOLTAGE"): "ESC_UV_001",
    ("ESC", "OVER_VOLTAGE"):  "ESC_OV_001",
    ("ESC", "RAPID_DROP"):    "ESC_RD_001",
    # FC — 모델 번호별 매핑 (_001: CUAV V6X, _002: Cube Orange+, _003: X7+pro)
    ("FC",     "UNDER_VOLTAGE"): "FC_UV_001",
    ("FC",     "OVER_VOLTAGE"):  "FC_OV_001",
    ("FC_001", "UNDER_VOLTAGE"): "FC_UV_001",
    ("FC_001", "OVER_VOLTAGE"):  "FC_OV_001",
    ("FC_002", "UNDER_VOLTAGE"): "FC_UV_002",
    ("FC_002", "OVER_VOLTAGE"):  "FC_OV_002",
    ("FC_003", "UNDER_VOLTAGE"): "FC_UV_003",
    ("FC_003", "OVER_VOLTAGE"):  "FC_OV_003",
    # GPS — 모델 번호별 매핑 (_001: MG-F10, _002: H-RTK, _003: m10)
    ("GPS",     "UNDER_VOLTAGE"): "GPS_UV_001",
    ("GPS",     "OVER_VOLTAGE"):  "GPS_OV_001",
    ("GPS_001", "UNDER_VOLTAGE"): "GPS_UV_001",
    ("GPS_001", "OVER_VOLTAGE"):  "GPS_OV_001",
    ("GPS_002", "UNDER_VOLTAGE"): "GPS_UV_002",
    ("GPS_002", "OVER_VOLTAGE"):  "GPS_OV_002",
    ("GPS_003", "UNDER_VOLTAGE"): "GPS_UV_003",
    ("GPS_003", "OVER_VOLTAGE"):  "GPS_OV_003",
    # TEL — 모델 번호별 매핑 (_001: UniRC7, _002: Herelink, _003: HM30)
    ("TEL",     "UNDER_VOLTAGE"): "TEL_UV_001",
    ("TEL",     "OVER_VOLTAGE"):  "TEL_OV_001",
    ("TEL_001", "UNDER_VOLTAGE"): "TEL_UV_001",
    ("TEL_001", "OVER_VOLTAGE"):  "TEL_OV_001",
    ("TEL_002", "UNDER_VOLTAGE"): "TEL_UV_002",
    ("TEL_002", "OVER_VOLTAGE"):  "TEL_OV_002",
    ("TEL_003", "UNDER_VOLTAGE"): "TEL_UV_003",
    ("TEL_003", "OVER_VOLTAGE"):  "TEL_OV_003",
    # BEC — 모델 번호별 매핑 (_001: 16.5~80V, _002: 9~80V)
    ("BEC",     "UNDER_VOLTAGE"): "BEC_UV_001",
    ("BEC",     "OVER_VOLTAGE"):  "BEC_OV_001",
    ("BEC_001", "UNDER_VOLTAGE"): "BEC_UV_001",
    ("BEC_001", "OVER_VOLTAGE"):  "BEC_OV_001",
    ("BEC_002", "UNDER_VOLTAGE"): "BEC_UV_002",
    ("BEC_002", "OVER_VOLTAGE"):  "BEC_OV_002",
    # CAM — 모델 번호별 매핑 (_001: A8, _002: ZT6 mini)
    ("CAM",     "UNDER_VOLTAGE"): "Cam_UV_001",
    ("CAM",     "OVER_VOLTAGE"):  "Cam_OV_001",
    ("CAM_001", "UNDER_VOLTAGE"): "Cam_UV_001",
    ("CAM_001", "OVER_VOLTAGE"):  "Cam_OV_001",
    ("CAM_002", "UNDER_VOLTAGE"): "Cam_UV_002",
    ("CAM_002", "OVER_VOLTAGE"):  "Cam_OV_002",
    # MOT/PWR — 모델 번호별 매핑 (_001: Xrotor X6, _002: 6015, _003: 6215 IPE)
    ("MOT",     "UNDER_VOLTAGE"): "PWR_UV_001",
    ("MOT",     "OVER_VOLTAGE"):  "PWR_OV_001",
    ("MOT_001", "UNDER_VOLTAGE"): "PWR_UV_001",
    ("MOT_001", "OVER_VOLTAGE"):  "PWR_OV_001",
    ("MOT_002", "UNDER_VOLTAGE"): "PWR_UV_002",
    ("MOT_002", "OVER_VOLTAGE"):  "PWR_OV_002",
    ("MOT_003", "UNDER_VOLTAGE"): "PWR_UV_003",
    ("MOT_003", "OVER_VOLTAGE"):  "PWR_OV_003",
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
                awg=item.get('awg', ''),
                connector=item.get('connector', ''),
                connector_rated_current=item.get('connector_rated_current', ''),
            )
            self._db[fc.code] = fc

    def get_code(self, component_id: str, state: VoltageState) -> Optional[str]:
        key = (component_id, state.value)
        return _COMPONENT_STATE_MAP.get(key)

    def get_fault_code_obj(self, code: str) -> Optional[FaultCode]:
        return self._db.get(code)

    def get_all(self) -> Dict[str, FaultCode]:
        return dict(self._db)