# FaultCode model representing a specific electrical fault code entry
from dataclasses import dataclass
from models.diagnosis_result import Severity


@dataclass
class FaultCode:
    code: str
    component_id: str
    fault_type: str
    severity: Severity
    description_ko: str
    maintenance_ko: str
