# Builds human-readable decision messages from a DiagnosisResult
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity

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
