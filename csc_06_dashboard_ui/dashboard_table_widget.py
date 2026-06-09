# Component status table with colored state/severity badges
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from models.component import Component
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity

HEADERS = ["부품", "모델", "정격(V)", "현재(V)", "상태", "고장코드", "심각도", "정비 조치"]

_STATE_STYLE = {
    VoltageState.NORMAL:        ("NORMAL",       "#EAF3DE", "#3B6D11"),
    VoltageState.UNDER_VOLTAGE: ("저전압 (UV)",   "#FAEEDA", "#854F0B"),
    VoltageState.OVER_VOLTAGE:  ("과전압 (OV)",   "#FCEBEB", "#A32D2D"),
    VoltageState.NO_DATA:       ("데이터없음",    "#FBEAF0", "#993556"),
    VoltageState.SENSOR_ERROR:  ("센서오류",      "#EEEDFE", "#4A3F9E"),
    VoltageState.RAPID_DROP:    ("급강하",        "#E6F1FB", "#185FA5"),
}
_SEV_STYLE = {
    Severity.LOW:      ("#EAF3DE", "#3B6D11"),
    Severity.MEDIUM:   ("#E6F1FB", "#185FA5"),
    Severity.HIGH:     ("#FAEEDA", "#854F0B"),
    Severity.CRITICAL: ("#FCEBEB", "#A32D2D"),
}
_ROW_FAULT_BG = QColor("#FFF8F0")


def _badge(text: str, bg: str, fg: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(4, 2, 4, 2)
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:4px;"
        f" padding:1px 6px; font-size:10px; font-weight:600;"
    )
    lay.addWidget(lbl)
    return w


class DashboardTableWidget(QWidget):
    def __init__(self, components: list, parent=None):
        super().__init__(parent)
        self._components: Dict[str, Component] = {c.id: c for c in components}
        self._results: Dict[str, DiagnosisResult] = {}
        self._setup_ui()
        self._populate_initial()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("부품 상태 테이블")
        header.setStyleSheet("font-weight:600; font-size:12px; color:#344054;")
        layout.addWidget(header)

        self._table = QTableWidget(len(self._components), len(HEADERS))
        self._table.setHorizontalHeaderLabels(HEADERS)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setStyleSheet(
            "QTableWidget { border:1px solid #D3D1C7; border-radius:6px; "
            "  gridline-color:#EAE9E3; font-size:11px; }"
            "QHeaderView::section { background:#F4F3EF; color:#344054; "
            "  border:none; border-bottom:1px solid #D3D1C7; padding:4px; font-weight:600; }"
        )
        self._table.setColumnWidth(0, 80)
        self._table.setColumnWidth(1, 160)
        self._table.setColumnWidth(2, 110)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 100)
        self._table.setColumnWidth(5, 110)
        self._table.setColumnWidth(6, 80)
        layout.addWidget(self._table)

    def _populate_initial(self):
        for row, comp in enumerate(sorted(self._components.values(), key=lambda c: c.priority)):
            self._set_row(row, comp, None)

    def _set_row(self, row: int, comp: Component, result: Optional[DiagnosisResult]):
        def _item(text: str) -> QTableWidgetItem:
            it = QTableWidgetItem(text)
            it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            return it

        self._table.setItem(row, 0, _item(comp.name))
        self._table.setItem(row, 1, _item(comp.model_name))
        self._table.setItem(row, 2, _item(comp.rated_range_str))

        if result is None:
            self._table.setItem(row, 3, _item("—"))
            txt, bg, fg = _STATE_STYLE[VoltageState.NO_DATA]
            self._table.setCellWidget(row, 4, _badge(txt, bg, fg))
            self._table.setItem(row, 5, _item("—"))
            self._table.setCellWidget(row, 6, _badge("—", "#F4F3EF", "#888"))
            self._table.setItem(row, 7, _item("—"))
            return

        volt_str = f"{result.current_voltage:.2f}V" if result.current_voltage is not None else "N/A"
        self._table.setItem(row, 3, _item(volt_str))

        txt, bg, fg = _STATE_STYLE.get(result.state, ("?", "#FFF", "#000"))
        self._table.setCellWidget(row, 4, _badge(txt, bg, fg))
        self._table.setItem(row, 5, _item(result.fault_code or "—"))

        sev_bg, sev_fg = _SEV_STYLE.get(result.severity, ("#FFF", "#000"))
        self._table.setCellWidget(row, 6, _badge(result.severity.value, sev_bg, sev_fg))
        action_short = (result.maintenance_action.split('\n')[0])[:60]
        self._table.setItem(row, 7, _item(action_short))

        row_bg = _ROW_FAULT_BG if result.is_fault else QColor("#FFFFFF")
        for col in [0, 1, 2, 3, 5, 7]:
            item = self._table.item(row, col)
            if item:
                item.setBackground(row_bg)

    def update_result(self, result: DiagnosisResult):
        self._results[result.component_id] = result
        comps_sorted = sorted(self._components.values(), key=lambda c: c.priority)
        for row, comp in enumerate(comps_sorted):
            if comp.id == result.component_id:
                self._set_row(row, comp, result)
                break

    def reset(self):
        self._results.clear()
        for row, comp in enumerate(sorted(self._components.values(), key=lambda c: c.priority)):
            self._set_row(row, comp, None)
