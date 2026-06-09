# Assembles a complete DiagnosisResult from classification outputs
from datetime import datetime
from typing import Optional
from models.component import Component
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity


class DiagnosisResultBuilder:
    def build(
        self,
        component: Component,
        voltage: Optional[float],
        state: VoltageState,
        severity: Severity,
        fault_code: Optional[str],
        maintenance_action: str,
    ) -> DiagnosisResult:
        return DiagnosisResult(
            component_id=component.id,
            state=state,
            current_voltage=voltage,
            fault_code=fault_code,
            severity=severity,
            maintenance_action=maintenance_action,
            diagnosed_at=datetime.now(),
        )
