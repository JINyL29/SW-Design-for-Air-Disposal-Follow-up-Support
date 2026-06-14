# Fault injection scenario panel and diagnosis result preview for the simulation UI
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal
from models.component import Component
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity

_SCENARIO_STYLES = {
    "NORMAL":        ("#EAF3DE", "#639922", "Normal"),
    "UNDER_VOLTAGE": ("#FCEBEB", "#E24B4A", "Under-Voltage"),
    "OVER_VOLTAGE":  ("#FCEBEB", "#E24B4A", "Over-Voltage"),
    "NO_DATA":       ("#FBEAF0", "#D4537E", "No Data"),
    "SENSOR_ERROR":  ("#EEEDFE", "#7F77DD", "Sensor Error"),
    "RAPID_DROP":    ("#E6F1FB", "#378ADD", "Rapid Drop"),
}
_SCENARIO_ORDER = [
    "NORMAL", "UNDER_VOLTAGE",
    "OVER_VOLTAGE", "NO_DATA",
    "SENSOR_ERROR", "RAPID_DROP",
]

_STATE_KO = {
    VoltageState.NORMAL:        "정상",
    VoltageState.UNDER_VOLTAGE: "저전압 (UV)",
    VoltageState.OVER_VOLTAGE:  "과전압 (OV)",
    VoltageState.NO_DATA:       "데이터 없음",
    VoltageState.SENSOR_ERROR:  "센서 오류",
    VoltageState.RAPID_DROP:    "급격한 전압 강하",
}
_SEV_COLORS = {
    Severity.CRITICAL: ("#FCEBEB", "#A32D2D"),
    Severity.HIGH:     ("#FAEEDA", "#854F0B"),
    Severity.MEDIUM:   ("#E6F1FB", "#185FA5"),
    Severity.LOW:      ("#EAF3DE", "#3B6D11"),
}


def _preview_card(title: str, value: str, bg: str, fg: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background:{bg}; border:1px solid {fg};"
        f" border-radius:8px; padding:4px; }}"
    )
    lay = QVBoxLayout(f)
    lay.setContentsMargins(10, 8, 10, 8)
    lay.setSpacing(4)
    t = QLabel(title)
    t.setStyleSheet(f"font-size:10px; color:{fg}; font-weight:600; border:none;")
    v = QLabel(value)
    v.setStyleSheet(f"font-size:16px; font-weight:700; color:{fg}; border:none;")
    v.setWordWrap(True)
    lay.addWidget(t)
    lay.addWidget(v)
    return f


class OperatorInjectPanel(QWidget):
    scenario_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # Section header
        inj_lbl = QLabel("고장 시나리오 주입")
        inj_lbl.setStyleSheet("font-size:12px; font-weight:700; color:#344054;")
        lay.addWidget(inj_lbl)

        hint = QLabel("시나리오를 클릭하면 해당 전압이 자동 주입되고 진단이 실행됩니다.")
        hint.setStyleSheet("font-size:10px; color:#667085;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(8)
        self._scenario_btns = {}
        for i, key in enumerate(_SCENARIO_ORDER):
            bg, fg, label = _SCENARIO_STYLES[key]
            btn = QPushButton(label)
            btn.setStyleSheet(
                f"QPushButton {{ background:{bg}; color:{fg}; border:1.5px solid {fg};"
                f" border-radius:8px; padding:10px 6px; font-size:12px; font-weight:700; }}"
                f"QPushButton:hover {{ background:{fg}; color:#FFFFFF; }}"
            )
            btn.clicked.connect(lambda _=False, k=key: self.scenario_selected.emit(k))
            grid.addWidget(btn, i // 2, i % 2)
            self._scenario_btns[key] = btn
        lay.addLayout(grid)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:#D3D1C7; max-height:1px; border:none;")
        lay.addWidget(div)

        # Preview cards header
        preview_lbl = QLabel("진단 결과 프리뷰")
        preview_lbl.setStyleSheet(
            "font-size:12px; font-weight:700; color:#344054;"
        )
        lay.addWidget(preview_lbl)

        self._prev_state  = _preview_card("진단 상태",  "—", "#F4F3EF", "#667085")
        self._prev_code   = _preview_card("고장 코드",  "—", "#F4F3EF", "#667085")
        self._prev_sev    = _preview_card("심각도",     "—", "#F4F3EF", "#667085")
        self._prev_dev    = _preview_card("편차 (%)",   "—", "#F4F3EF", "#667085")
        self._prev_wire   = _preview_card("전선 규격",  "—", "#F4F3EF", "#667085")

        for card in [self._prev_state, self._prev_code, self._prev_sev,
                     self._prev_dev, self._prev_wire]:
            lay.addWidget(card)

        lay.addStretch()

    def update_preview(self, result: DiagnosisResult, deviation_pct: Optional[float] = None, fault_code_obj=None):
        state_txt = _STATE_KO.get(result.state, result.state.value)
        sev_bg, sev_fg = _SEV_COLORS.get(result.severity, ("#F4F3EF", "#667085"))
        volt = (f"{result.current_voltage:.2f} V" if result.current_voltage is not None else "N/A")

        self._replace_card(
            self._prev_state, "진단 상태", f"{state_txt}\n({volt})",
            sev_bg if result.is_fault else "#F4F3EF",
            sev_fg if result.is_fault else "#667085",
        )
        self._replace_card(
            self._prev_code, "고장 코드", result.fault_code or "없음",
            sev_bg if result.fault_code else "#F4F3EF",
            sev_fg if result.fault_code else "#667085",
        )
        self._replace_card(
            self._prev_sev, "심각도", result.severity.value,
            sev_bg, sev_fg,
        )
        dev_str = f"{deviation_pct:+.1f}%" if deviation_pct is not None else "—"
        self._replace_card(self._prev_dev, "편차 (%)", dev_str, "#F4F3EF", "#344054")

        if fault_code_obj and (fault_code_obj.awg or fault_code_obj.connector):
            wire_parts = []
            if fault_code_obj.awg:
                wire_parts.append(fault_code_obj.awg)
            if fault_code_obj.connector:
                wire_parts.append(fault_code_obj.connector)
            if fault_code_obj.connector_rated_current:
                wire_parts.append(fault_code_obj.connector_rated_current)
            wire_str = "  /  ".join(wire_parts)
            wire_bg, wire_fg = "#E6F1FB", "#185FA5"
        else:
            wire_str = "정보 없음"
            wire_bg, wire_fg = "#F4F3EF", "#667085"
        self._replace_card(self._prev_wire, "전선 규격", wire_str, wire_bg, wire_fg)

    def _replace_card(self, old: QFrame, title: str, value: str, bg: str, fg: str):
        lay = self.layout()
        idx = lay.indexOf(old)
        if idx < 0:
            return
        new = _preview_card(title, value, bg, fg)
        lay.removeWidget(old)
        old.deleteLater()
        lay.insertWidget(idx, new)
        if old is self._prev_state:
            self._prev_state = new
        elif old is self._prev_code:
            self._prev_code = new
        elif old is self._prev_sev:
            self._prev_sev = new
        elif old is self._prev_dev:
            self._prev_dev = new
        elif old is self._prev_wire:
            self._prev_wire = new

    def reset_preview(self):
        titles = {
            "_prev_state": "진단 상태",
            "_prev_code":  "고장 코드",
            "_prev_sev":   "심각도",
            "_prev_dev":   "편차 (%)",
            "_prev_wire":  "전선 규격",
        }
        for attr, title in titles.items():
            old = getattr(self, attr)
            self._replace_card(old, title, "—", "#F4F3EF", "#667085")
