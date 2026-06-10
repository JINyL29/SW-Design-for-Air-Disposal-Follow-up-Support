# Builds human-readable decision messages from a DiagnosisResult
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity

# ── 배선도 토폴로지 영향 맵 ────────────────────────────────────────────────────
# 실선(전력선) 기준 양방향 영향 맵
#
# upstream  : 나에게 전력을 주는 쪽 → 고장 원인일 수 있으므로 확인
# downstream: 내가 전력을 주는 쪽  → 내 이상으로 피해받으므로 확인
#
# 배선도 실선 엣지:
#   BAT → PDB → ESC
#              → BEC → FC  → GPS
#                    → TEL
#                    → CAM

_UPSTREAM_IMPACT = {
    "PDB": ["BAT"],
    "BEC": ["PDB"],
    "ESC": ["PDB"],
    "FC":  ["BEC"],
    "TEL": ["BEC"],
    "CAM": ["BEC"],
    "GPS": ["FC"],
}

_DOWNSTREAM_IMPACT = {
    "BAT": ["PDB"],
    "PDB": ["ESC", "BEC"],
    "BEC": ["FC", "TEL", "CAM"],
    "FC":  ["GPS"],
}

_STATE_KO = {
    VoltageState.NORMAL:        "정상",
    VoltageState.UNDER_VOLTAGE: "저전압",
    VoltageState.OVER_VOLTAGE:  "과전압",
    VoltageState.NO_DATA:       "데이터 없음",
    VoltageState.SENSOR_ERROR:  "센서 오류",
    VoltageState.RAPID_DROP:    "급격한 전압 강하",
}

_SEV_KO = {
    Severity.LOW:      "낮음",
    Severity.MEDIUM:   "보통",
    Severity.HIGH:     "높음",
    Severity.CRITICAL: "긴급",
}


class DecisionMessageBuilder:
    def build_summary(self, result: DiagnosisResult) -> str:
        ts = result.diagnosed_at.strftime("%H:%M:%S")
        state_ko = _STATE_KO.get(result.state, result.state.value)
        sev_ko = _SEV_KO.get(result.severity, result.severity.value)
        volt_str = f"{result.current_voltage:.2f}V" if result.current_voltage is not None else "N/A"
        code_str = result.fault_code or "없음"
        return (
            f"[{ts}] [{result.severity.value}] {result.component_id} — "
            f"상태: {state_ko} | 전압: {volt_str} | 코드: {code_str} | 심각도: {sev_ko}"
        )

    def build_terminal_log(self, result: DiagnosisResult) -> str:
        ts = result.diagnosed_at.strftime("%H:%M:%S")
        volt_str = f"{result.current_voltage:.2f}V" if result.current_voltage is not None else "N/A"
        code_str = result.fault_code or "N/A"
        return (
            f"[{ts}] [{result.severity.value}] {code_str} — "
            f"{result.component_id} {volt_str}"
        )

    def state_ko(self, result: DiagnosisResult) -> str:
        return _STATE_KO.get(result.state, result.state.value)

    def build_impact_message(self, result: DiagnosisResult) -> str:
        """
        고장 부품의 연쇄 영향 메시지 생성.
        정상(NORMAL) 상태면 빈 문자열 반환.

        예시:
          BEC 저전압 → "⚠ BEC 이상 감지 → 직접 영향: FC, Telemetry, CAM 전압 확인 필요"
          FC 과전압  → "⚠ FC 이상 감지 → 직접 영향: GPS | 신호 영향: TEL, ESC 동작 확인 필요"
        """
        if result.state == VoltageState.NORMAL:
            return ""

        cid = result.component_id
        upstream   = _UPSTREAM_IMPACT.get(cid, [])
        downstream = _DOWNSTREAM_IMPACT.get(cid, [])

        if not upstream and not downstream:
            return ""

        parts = []
        if upstream:
            parts.append(f"전력 공급원 확인 필요: {chr(44).join(upstream)}")
        if downstream:
            parts.append(f"영향 부품 확인 필요: {chr(44).join(downstream)}")

        return f"⚠ {cid} 이상 감지 → " + " | ".join(parts)
