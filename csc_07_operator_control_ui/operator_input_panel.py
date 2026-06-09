# Component selector and voltage input panel for the simulation UI
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QLineEdit, QProgressBar, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator
from models.component import Component
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity
from csc_02_input_control.csu_02_voltage_input_handler import VoltageInputHandler

_SEV_BADGE = {
    Severity.CRITICAL: ("CRITICAL", "#FCEBEB", "#A32D2D"),
    Severity.HIGH:     ("HIGH",     "#FAEEDA", "#854F0B"),
    Severity.MEDIUM:   ("MEDIUM",   "#E6F1FB", "#185FA5"),
    Severity.LOW:      ("LOW",      "#EAF3DE", "#3B6D11"),
}


class OperatorInputPanel(QWidget):
    component_selected = Signal(str)
    voltage_changed = Signal(float)

    def __init__(self, components: list, parent=None):
        super().__init__(parent)
        self._components: Dict[str, Component] = {c.id: c for c in components}
        self._handler = VoltageInputHandler()
        self._results: Dict[str, DiagnosisResult] = {}
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # Section header
        lbl = QLabel("부품 선택")
        lbl.setStyleSheet("font-size:12px; font-weight:700; color:#344054;")
        lay.addWidget(lbl)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { border:1px solid #D3D1C7; border-radius:6px;"
            " background:#FFFFFF; color:#1A2B3C; font-size:12px; }"
            "QListWidget::item { padding:7px 10px; color:#1A2B3C; }"
            "QListWidget::item:selected { background:#E6F1FB; color:#185FA5; }"
            "QListWidget::item:hover { background:#F4F3EF; }"
        )
        self._list.setMinimumHeight(260)
        for comp in sorted(self._components.values(), key=lambda c: c.priority):
            item = QListWidgetItem(f"{comp.name}  ({comp.model_name[:22]})")
            item.setData(Qt.ItemDataRole.UserRole, comp.id)
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_component_changed)
        lay.addWidget(self._list)

        # Voltage input section
        v_frame = QFrame()
        v_frame.setStyleSheet(
            "QFrame { background:#FFFFFF; border:1px solid #D3D1C7; border-radius:8px; }"
        )
        v_lay = QVBoxLayout(v_frame)
        v_lay.setContentsMargins(12, 10, 12, 10)
        v_lay.setSpacing(8)

        v_title = QLabel("전압 직접 입력")
        v_title.setStyleSheet("font-size:12px; font-weight:700; color:#344054; border:none;")
        v_lay.addWidget(v_title)

        self._hint = QLabel("부품을 선택하면 정격 범위가 표시됩니다")
        self._hint.setStyleSheet("font-size:11px; color:#667085; border:none;")
        self._hint.setWordWrap(True)
        v_lay.addWidget(self._hint)

        row = QWidget()
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.setSpacing(6)
        self._volt_input = QLineEdit()
        self._volt_input.setPlaceholderText("전압 입력 (V)")
        self._volt_input.setValidator(QDoubleValidator(0.0, 9999.0, 3))
        self._volt_input.setStyleSheet(
            "QLineEdit { border:1px solid #D3D1C7; border-radius:6px; padding:6px 10px;"
            " font-size:14px; background:#FAFAF8; color:#1A2B3C; }"
            "QLineEdit:focus { border-color:#378ADD; }"
        )
        self._volt_input.textChanged.connect(self._on_voltage_text_changed)
        row_l.addWidget(self._volt_input)
        unit = QLabel("V")
        unit.setStyleSheet("font-size:14px; font-weight:600; color:#344054; border:none;")
        row_l.addWidget(unit)
        v_lay.addWidget(row)

        self._gauge = QProgressBar()
        self._gauge.setRange(0, 1000)
        self._gauge.setValue(0)
        self._gauge.setTextVisible(False)
        self._gauge.setFixedHeight(10)
        self._gauge.setStyleSheet(
            "QProgressBar { background:#EAE9E3; border-radius:5px; }"
            "QProgressBar::chunk { background:#378ADD; border-radius:5px; }"
        )
        v_lay.addWidget(self._gauge)

        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet("font-size:11px; color:#E24B4A; border:none;")
        v_lay.addWidget(self._err_lbl)

        lay.addWidget(v_frame)
        lay.addStretch()

        self._list.setCurrentRow(0)

    def _on_component_changed(self, current, _previous):
        if current is None:
            return
        cid = current.data(Qt.ItemDataRole.UserRole)
        comp = self._components.get(cid)
        if comp:
            self._hint.setText(
                f"정상: {comp.voltage_warn_high:.2f} ~ {comp.voltage_max:.2f} V  |  "
                f"경고: {comp.voltage_min:.2f} ~ {comp.voltage_warn_high - 0.01:.2f} V"
            )
            self.component_selected.emit(cid)
            self._update_gauge()

    def _on_voltage_text_changed(self, text: str):
        self._err_lbl.setText("")
        self._update_gauge()
        try:
            v = float(text)
            self.voltage_changed.emit(v)
        except ValueError:
            pass

    def _update_gauge(self):
        cid = self.selected_component_id()
        comp = self._components.get(cid) if cid else None
        if comp is None:
            return
        try:
            v = float(self._volt_input.text())
        except ValueError:
            return
        pct = self._handler.compute_gauge_pct(v, comp)
        self._gauge.setValue(int(pct * 1000))

    def selected_component_id(self) -> Optional[str]:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def get_voltage(self) -> Optional[float]:
        try:
            return float(self._volt_input.text())
        except ValueError:
            return None

    def set_voltage(self, value: float):
        self._volt_input.setText(str(value))

    def show_error(self, msg: str):
        self._err_lbl.setText(msg)

    def update_result(self, result: DiagnosisResult):
        self._results[result.component_id] = result
        self._refresh_list_badges()

    def _refresh_list_badges(self):
        for i in range(self._list.count()):
            item = self._list.item(i)
            cid = item.data(Qt.ItemDataRole.UserRole)
            result = self._results.get(cid)
            comp = self._components.get(cid)
            if comp is None:
                continue
            base = f"{comp.name}  ({comp.model_name[:22]})"
            if result and result.is_fault:
                item.setText(f"{base}  ⚠ {result.severity.value}")
            else:
                item.setText(base)

    def reset(self):
        self._results.clear()
        self._volt_input.clear()
        self._gauge.setValue(0)
        self._err_lbl.setText("")
        self._refresh_list_badges()
