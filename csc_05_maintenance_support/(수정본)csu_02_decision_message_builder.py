# Builds human-readable decision messages from a DiagnosisResult
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity

# ── 배선도 토폴로지 영향 맵 ────────────────────────────────────────────────────
# dashboard_wiring_scene.py의 EDGES 리스트 기반
# 실선(dashed=False) → 직접 전력 공급 영향
# 점선(dashed=True)  → 신호(PWM/UART) 영향
_DIRECT_IMPACT = {
    "BAT": ["PDB"],
    "PDB": ["ESC", "BEC"],
    "BEC": ["FC", "TEL", "CAM"],
    "FC":  ["GPS"],
}
_SIGNAL_IMPACT = {
    "ESC": ["MOT"],
    "FC":  ["TEL", "ESC"],
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
        parts = []

        direct = _DIRECT_IMPACT.get(cid, [])
        if direct:
            parts.append(f"직접 영향: {', '.join(direct)} 전압 확인 필요")

        signal = _SIGNAL_IMPACT.get(cid, [])
        if signal:
            parts.append(f"신호 영향: {', '.join(signal)} 동작 확인 필요")

        if not parts:
            return ""

        return f"⚠ {cid} 이상 감지 → " + " | ".join(parts)