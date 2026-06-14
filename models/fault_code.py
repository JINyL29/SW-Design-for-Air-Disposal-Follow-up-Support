# FaultCode model representing a specific electrical fault code entry
from dataclasses import dataclass, field
from models.diagnosis_result import Severity


@dataclass
class FaultCode:
    code: str
    component_id: str
    fault_type: str
    severity: Severity
    description_ko: str
    maintenance_ko: str
    # ICD 기반 추가 필드 (기본값 제공으로 하위 호환 유지)
    awg: str = ""                      # 예: "24 AWG"
    connector: str = ""                # 예: "GH1.25"
    connector_rated_current: str = ""  # 예: "1A"