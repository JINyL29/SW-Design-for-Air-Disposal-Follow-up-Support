# Realistic fault scenario definitions based on drone electrical topology
# BAT → PDB → ESC → MOT
#           → BEC → FC  → GPS
#                 → TEL
#                 → CAM
import random
from typing import Dict, List, Optional, Tuple, Callable

# ── Fault voltage ranges (based on component_voltage_db.json) ────────────────
# UV_CRIT  : below critical_low  (hard fault)
# UV_WARN  : [critical_low, normal_min)  (warning zone)
# OV       : above normal_max

_UV_CRIT = {
    "BAT": (34.0, 37.9),
    "ESC": (36.0, 39.9),
    "FC":  (3.5,  4.49),
    "GPS": (3.5,  4.49),
    "TEL": (8.0,  10.9),
    "BEC": (8.0,  10.9),
    "CAM": (7.0,   9.9),
    "MOT": (36.0, 39.9),
}
_UV_WARN = {
    "BAT": (38.0, 39.9),
    "ESC": (40.0, 44.3),
    "FC":  (4.50, 4.74),
    "GPS": (4.50, 4.74),
    "TEL": (11.0, 11.9),
    "BEC": (11.0, 11.7),
    "CAM": (10.0, 11.0),
    "MOT": (40.0, 44.3),
}
_OV = {
    "BAT": (51.9, 55.0),
    "ESC": (51.9, 55.0),
    "FC":  (5.46,  6.0),
    "GPS": (5.26,  6.0),
    "TEL": (76.1, 80.0),
    "BEC": (12.9, 15.0),
    "CAM": (22.3, 25.0),
    "MOT": (51.9, 55.0),
}


def _uv(cid: str) -> float:
    """Random under-voltage: 70% critical, 30% warning."""
    if random.random() < 0.7:
        lo, hi = _UV_CRIT[cid]
    else:
        lo, hi = _UV_WARN[cid]
    return round(random.uniform(lo, hi), 2)


def _ov(cid: str) -> float:
    lo, hi = _OV[cid]
    return round(random.uniform(lo, hi), 2)


# RAPID_DROP: voltage just below critical_low (급강하 직전 측정값)
_RAPID_DROP_V = {
    "BAT": (35.5, 37.5),  # critical_low = 38.0
    "ESC": (37.5, 39.5),  # critical_low = 40.0
}

def _rd(cid: str) -> float:
    lo, hi = _RAPID_DROP_V[cid]
    return round(random.uniform(lo, hi), 2)


# ── 18 Scenarios ─────────────────────────────────────────────────────────────
# Each scenario:
#   id            : int
#   name          : str
#   description   : str
#   cascade_order : list[comp_id]  — order faults appear (root → leaf)
#   faults        : dict[comp_id -> (scenario_key, volt_fn | None)]
#       scenario_key : "UNDER_VOLTAGE" | "OVER_VOLTAGE" | "RAPID_DROP"
#                      | "NO_DATA" | "SENSOR_ERROR"
#       volt_fn      : callable() -> float, or None for non-voltage faults

SCENARIOS: List[Dict] = [
    # ── 독립 고장 (1~5) ──────────────────────────────────────────────────────
    {
        "id": 1,
        "name": "MOT 과전압 (배터리 셀 수 불일치)",
        "description": "배터리 셀 수 불일치로 모터에 과전압 공급",
        "cascade_order": ["MOT"],
        "faults": {
            "MOT": ("OVER_VOLTAGE", lambda: _ov("MOT")),
        },
    },
    {
        "id": 2,
        "name": "GPS 단독 고장 (모듈 내부 불량)",
        "description": "GPS 모듈 자체 결함으로 인한 전압 이상",
        "cascade_order": ["GPS"],
        "faults": {
            "GPS": ("UNDER_VOLTAGE", lambda: _uv("GPS")),
        },
    },
    {
        "id": 3,
        "name": "TEL 단독 고장 (커넥터 접촉 불량)",
        "description": "XT30 커넥터 접촉 불량으로 텔레메트리 전원 불안정",
        "cascade_order": ["TEL"],
        "faults": {
            "TEL": ("UNDER_VOLTAGE", lambda: _uv("TEL")),
        },
    },
    {
        "id": 4,
        "name": "CAM 단독 고장 (16AWG 전원 케이블 단선)",
        "description": "16 AWG XT30 전원 케이블 단선으로 카메라 전원 상실",
        "cascade_order": ["CAM"],
        "faults": {
            "CAM": ("UNDER_VOLTAGE", lambda: _uv("CAM")),
        },
    },
    {
        "id": 5,
        "name": "BAT 경고 수준 방전",
        "description": "배터리 경고 구간 진입 — 즉시 복귀 필요",
        "cascade_order": ["BAT"],
        "faults": {
            "BAT": ("UNDER_VOLTAGE", lambda: round(random.uniform(38.0, 39.9), 2)),
        },
    },
    # ── 2단계 캐스케이딩 (6~10) ──────────────────────────────────────────────
    {
        "id": 6,
        "name": "ESC 과전압 → MOT 과전압",
        "description": "ESC 입력 과전압이 모터 구동 전압 초과로 이어짐",
        "cascade_order": ["ESC", "MOT"],
        "faults": {
            "ESC": ("OVER_VOLTAGE", lambda: _ov("ESC")),
            "MOT": ("OVER_VOLTAGE", lambda: _ov("MOT")),
        },
    },
    {
        "id": 7,
        "name": "ESC 저전압 → MOT 저전압 (추력 저하)",
        "description": "12AWG 배선 저항 증가로 ESC 입력 전압 저하 → 모터 추력 감소",
        "cascade_order": ["ESC", "MOT"],
        "faults": {
            "ESC": ("UNDER_VOLTAGE", lambda: _uv("ESC")),
            "MOT": ("UNDER_VOLTAGE", lambda: _uv("MOT")),
        },
    },
    {
        "id": 8,
        "name": "FC 저전압 → GPS 전원 상실",
        "description": "BEC→FC 24AWG GH1.25 배선 접촉 불량으로 FC 저전압 → GPS 전원 상실",
        "cascade_order": ["FC", "GPS"],
        "faults": {
            "FC":  ("UNDER_VOLTAGE", lambda: _uv("FC")),
            "GPS": ("UNDER_VOLTAGE", lambda: _uv("GPS")),
        },
    },
    {
        "id": 9,
        "name": "FC 과전압 → GPS 과전압 손상",
        "description": "BEC 과출력으로 FC 레귤레이터 이상 → GPS 과전압 손상 위험",
        "cascade_order": ["FC", "GPS"],
        "faults": {
            "FC":  ("OVER_VOLTAGE", lambda: _ov("FC")),
            "GPS": ("OVER_VOLTAGE", lambda: _ov("GPS")),
        },
    },
    {
        "id": 10,
        "name": "FC 센서 오류 → GPS 데이터 없음",
        "description": "FC 내부 센서 오류로 GPS 포트 데이터 수신 불가",
        "cascade_order": ["FC", "GPS"],
        "faults": {
            "FC":  ("SENSOR_ERROR", None),
            "GPS": ("NO_DATA",      None),
        },
    },
    # ── 중간 캐스케이딩 (11~13) ──────────────────────────────────────────────
    {
        "id": 11,
        "name": "BEC 저전압 → FC·TEL·CAM·GPS 연쇄 고장",
        "description": "14AWG XT90 BEC 입력 저전압 → BEC 출력 저하 → FC·TEL·CAM 동시 전원 오류 → GPS 상실",
        "cascade_order": ["BEC", "FC", "TEL", "CAM", "GPS"],
        "faults": {
            "BEC": ("UNDER_VOLTAGE", lambda: _uv("BEC")),
            "FC":  ("UNDER_VOLTAGE", lambda: _uv("FC")),
            "TEL": ("UNDER_VOLTAGE", lambda: _uv("TEL")),
            "CAM": ("UNDER_VOLTAGE", lambda: _uv("CAM")),
            "GPS": ("UNDER_VOLTAGE", lambda: _uv("GPS")),
        },
    },
    {
        "id": 12,
        "name": "BEC 과전압 → FC·TEL·CAM·GPS 과전압 손상",
        "description": "BEC 레귤레이터 이상 과출력 → FC·TEL·CAM 과전압 → GPS 손상",
        "cascade_order": ["BEC", "FC", "TEL", "CAM", "GPS"],
        "faults": {
            "BEC": ("OVER_VOLTAGE", lambda: _ov("BEC")),
            "FC":  ("OVER_VOLTAGE", lambda: _ov("FC")),
            "TEL": ("OVER_VOLTAGE", lambda: _ov("TEL")),
            "CAM": ("OVER_VOLTAGE", lambda: _ov("CAM")),
            "GPS": ("OVER_VOLTAGE", lambda: _ov("GPS")),
        },
    },
    {
        "id": 13,
        "name": "TEL·CAM 동시 고장 (BEC 출력 라인 부분 단선)",
        "description": "BEC 16AWG XT30 출력 라인 부분 단선 — FC는 정상, TEL·CAM만 전원 상실",
        "cascade_order": ["TEL", "CAM"],
        "faults": {
            "TEL": ("UNDER_VOLTAGE", lambda: _uv("TEL")),
            "CAM": ("UNDER_VOLTAGE", lambda: _uv("CAM")),
        },
    },
    # ── 전체 캐스케이딩 (14~16) ──────────────────────────────────────────────
    {
        "id": 14,
        "name": "BAT 완전 방전 — 전 계통 저전압",
        "description": "10AWG XT90 배터리 완전 방전 → PDB → 전 부품 저전압 연쇄",
        "cascade_order": ["BAT", "ESC", "MOT", "BEC", "FC", "TEL", "CAM", "GPS"],
        "faults": {
            "BAT": ("UNDER_VOLTAGE", lambda: _uv("BAT")),
            "ESC": ("UNDER_VOLTAGE", lambda: _uv("ESC")),
            "MOT": ("UNDER_VOLTAGE", lambda: _uv("MOT")),
            "BEC": ("UNDER_VOLTAGE", lambda: _uv("BEC")),
            "FC":  ("UNDER_VOLTAGE", lambda: _uv("FC")),
            "TEL": ("UNDER_VOLTAGE", lambda: _uv("TEL")),
            "CAM": ("UNDER_VOLTAGE", lambda: _uv("CAM")),
            "GPS": ("UNDER_VOLTAGE", lambda: _uv("GPS")),
        },
    },
    {
        "id": 15,
        "name": "BAT 과충전 — 전 계통 과전압",
        "description": "충전기 오작동으로 배터리 과충전 → 전 부품 과전압 연쇄",
        "cascade_order": ["BAT", "ESC", "MOT", "BEC", "FC", "TEL", "CAM", "GPS"],
        "faults": {
            "BAT": ("OVER_VOLTAGE", lambda: _ov("BAT")),
            "ESC": ("OVER_VOLTAGE", lambda: _ov("ESC")),
            "MOT": ("OVER_VOLTAGE", lambda: _ov("MOT")),
            "BEC": ("OVER_VOLTAGE", lambda: _ov("BEC")),
            "FC":  ("OVER_VOLTAGE", lambda: _ov("FC")),
            "TEL": ("OVER_VOLTAGE", lambda: _ov("TEL")),
            "CAM": ("OVER_VOLTAGE", lambda: _ov("CAM")),
            "GPS": ("OVER_VOLTAGE", lambda: _ov("GPS")),
        },
    },
    {
        "id": 16,
        "name": "BAT 급격한 전압 강하 — 비상 착륙",
        "description": "비행 중 배터리 급격한 방전 → RAPID_DROP → 전 계통 저전압 연쇄",
        "cascade_order": ["BAT", "ESC", "MOT", "BEC", "FC", "TEL", "CAM", "GPS"],
        "faults": {
            "BAT": ("RAPID_DROP",    lambda: _rd("BAT")),
            "ESC": ("UNDER_VOLTAGE", lambda: _uv("ESC")),
            "MOT": ("UNDER_VOLTAGE", lambda: _uv("MOT")),
            "BEC": ("UNDER_VOLTAGE", lambda: _uv("BEC")),
            "FC":  ("UNDER_VOLTAGE", lambda: _uv("FC")),
            "TEL": ("UNDER_VOLTAGE", lambda: _uv("TEL")),
            "CAM": ("UNDER_VOLTAGE", lambda: _uv("CAM")),
            "GPS": ("UNDER_VOLTAGE", lambda: _uv("GPS")),
        },
    },
    # ── 복합 시나리오 (17~18) ────────────────────────────────────────────────
    {
        "id": 17,
        "name": "PDB 접촉 불량 — ESC·BEC 동시 저전압",
        "description": "PDB 단자 접촉 불량으로 ESC·BEC 양측 동시 저전압 → 하위 전체 영향",
        "cascade_order": ["ESC", "MOT", "BEC", "FC", "TEL", "CAM", "GPS"],
        "faults": {
            "ESC": ("UNDER_VOLTAGE", lambda: _uv("ESC")),
            "MOT": ("UNDER_VOLTAGE", lambda: _uv("MOT")),
            "BEC": ("UNDER_VOLTAGE", lambda: _uv("BEC")),
            "FC":  ("UNDER_VOLTAGE", lambda: _uv("FC")),
            "TEL": ("UNDER_VOLTAGE", lambda: _uv("TEL")),
            "CAM": ("UNDER_VOLTAGE", lambda: _uv("CAM")),
            "GPS": ("UNDER_VOLTAGE", lambda: _uv("GPS")),
        },
    },
    {
        "id": 18,
        "name": "ESC 급격한 전압 강하 → MOT 추력 불안정",
        "description": "ESC 내부 이상으로 급격한 전압 강하 → 모터 추력 불안정",
        "cascade_order": ["ESC", "MOT"],
        "faults": {
            "ESC": ("RAPID_DROP",    lambda: _rd("ESC")),
            "MOT": ("UNDER_VOLTAGE", lambda: _uv("MOT")),
        },
    },
]


SCENARIOS.append({
    "id": 19,
    "name": "전 계통 정상",
    "description": "모든 부품이 정상 전압 범위 내에서 작동 중",
    "cascade_order": [],
    "faults": {},
})


def get_random_scenario() -> Dict:
    return random.choice(SCENARIOS)


def get_scenario_by_id(scenario_id: int) -> Optional[Dict]:
    for s in SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return None
