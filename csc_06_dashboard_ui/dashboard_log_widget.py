# Scrollable color-coded log panel for system diagnosis events
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtGui import QFont, QColor, QTextCursor
from models.diagnosis_result import DiagnosisResult, Severity, VoltageState

_COLOR_MAP = {
    Severity.CRITICAL: "#F09595",
    Severity.HIGH:     "#FAC775",
    Severity.MEDIUM:   "#A8D8FF",
    Severity.LOW:      "#5DCAA5",
}
_OK_COLOR   = "#5DCAA5"
_INFO_COLOR = "#8A9BB0"


class DashboardLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("시스템 로그")
        header.setStyleSheet("font-weight:600; font-size:12px; color:#344054;")
        layout.addWidget(header)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 9))
        self._log.setStyleSheet(
            "QTextEdit {"
            "  background:#0C2340; color:#A8C0D8;"
            "  border:1px solid #1A3A5C; border-radius:6px;"
            "  padding:6px;"
            "}"
        )
        self._log.setMinimumHeight(120)
        layout.addWidget(self._log)

    def append_result(self, result: DiagnosisResult):
        ts = result.diagnosed_at.strftime("%H:%M:%S")
        volt = f"{result.current_voltage:.2f}V" if result.current_voltage is not None else "N/A"

        if result.state == VoltageState.NORMAL:
            color = _OK_COLOR
            tag = "OK"
        else:
            color = _COLOR_MAP.get(result.severity, _INFO_COLOR)
            tag = result.severity.value

        code = result.fault_code or "—"
        html = (
            f'<span style="color:{_INFO_COLOR}">[{ts}]</span> '
            f'<span style="color:{color};font-weight:bold">[{tag}]</span> '
            f'<span style="color:#FFFFFF">{result.component_id}</span> '
            f'<span style="color:#A8C0D8">{volt} | {code}</span>'
        )
        self._append_html(html)

    def append_impact(self, message: str):
        """연쇄 영향 메시지 — 노란색으로 강조 출력"""
        html = f'<span style="color:#FAC775;font-weight:bold">{message}</span>'
        self._append_html(html)

    def append_info(self, message: str):
        ts_html = f'<span style="color:{_INFO_COLOR}">{message}</span>'
        self._append_html(ts_html)

    def _append_html(self, html: str):
        self._log.moveCursor(QTextCursor.MoveOperation.End)
        self._log.insertHtml(html + "<br>")
        self._log.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        self._log.clear()