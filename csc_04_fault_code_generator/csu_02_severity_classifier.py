# Classifies final severity combining zone and fault code base severity
from models.diagnosis_result import VoltageState, Severity
from csc_03_diagnosis_engine.csu_02_state_classifier import StateClassifier


class SeverityClassifier:
    def __init__(self):
        self._state_classifier = StateClassifier()

    def classify(self, state: VoltageState, zone: str) -> Severity:
        """Delegates to StateClassifier for consistent severity mapping."""
        return self._state_classifier.classify(state, zone)

    def label(self, severity: Severity) -> str:
        labels = {
            Severity.LOW:      "LOW",
            Severity.MEDIUM:   "MEDIUM",
            Severity.HIGH:     "HIGH",
            Severity.CRITICAL: "CRITICAL",
        }
        return labels.get(severity, "UNKNOWN")
