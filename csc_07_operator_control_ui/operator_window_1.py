# Virtual Fault Injection & Diagnostic Simulation UI – main window
from typing import Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity
from csc_01_component_db.csu_01_component_data_loader import get_component_loader
from csc_02_input_control.csu_03_scenario_input_handler import ScenarioInputHandler
from csc_02_input_control.csu_02_voltage_input_handler import VoltageInputHandler
from csc_03_diagnosis_engine.csu_01_voltage_comparator import VoltageComparator
from csc_03_diagnosis_engine.csu_02_state_classifier import StateClassifier
from csc_03_diagnosis_engine.csu_03_diagnosis_result_builder import DiagnosisResultBuilder
from csc_04_fault_code_generator.csu_01_fault_code_mapper import FaultCodeMapper
from csc_05_maintenance_support.csu_01_maintenance_action_mapper import MaintenanceActionMapper
from csc_05_maintenance_support.csu_02_decision_message_builder import DecisionMessageBuilder
from csc_07_operator_control_ui.operator_input_panel import OperatorInputPanel
from csc_07_operator_control_ui.operator_inject_panel import OperatorInjectPanel


class OperatorWindow(QMainWindow):
    diagnosis_done = Signal(object)   # DiagnosisResult
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loader = get_component_loader()
        self._components = {c.id: c for c in self._loader.get_all()}
        self._scenario_handler = ScenarioInputHandler()
        self._volt_handler = VoltageInputHandler()
        self._comparator = VoltageComparator()
        self._classifier = StateClassifier()
        self._builder = DiagnosisResultBuilder()
        self._fault_mapper = FaultCodeMapper()
        self._maint_mapper = MaintenanceActionMapper(self._fault_mapper)
        self._msg_builder = DecisionMessageBuilder()
        self._current_scenario: Optional[str] = None

        self.setWindowTitle("Virtual Fault Injection & Diagnostic Simulation UI")
        self.setMinimumSize(860, 900)
        self.resize(980, 1000)
        self._setup_ui()
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            "QMainWindow, QWidget { background:#F4F3EF; font-family:'Segoe UI',sans-serif; }"
            "QLabel { border:none; }"
        )

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        # Title
        title_row = QWidget()
        title_lay = QHBoxLayout(title_row)
        title_lay.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Virtual Fault Injection & Diagnostic Simulation")
        title.setStyleSheet(
            "font-size:16px; font-weight:700; color:#1A2B3C;"
            " padding-bottom:6px; border-bottom:2px solid #D3D1C7;"
        )
        subtitle = QLabel("드론 전기 계통 고장 주입 및 진단 시뮬레이션")
        subtitle.setStyleSheet(
            "font-size:11px; color:#667085; padding-bottom:6px;"
        )
        title_lay.addWidget(title)
        title_lay.addStretch()
        title_lay.addWidget(subtitle)
        outer.addWidget(title_row)

        # Three-column layout
        cols = QWidget()
        cols_lay = QHBoxLayout(cols)
        cols_lay.setContentsMargins(0, 0, 0, 0)
        cols_lay.setSpacing(12)

        self._input_panel = OperatorInputPanel(list(self._components.values()))
        self._input_panel.component_selected.connect(self._on_component_selected)
        cols_lay.addWidget(self._input_panel, 3)

        self._inject_panel = OperatorInjectPanel()
        self._inject_panel.scenario_selected.connect(self._on_scenario_selected)
        cols_lay.addWidget(self._inject_panel, 3)

        cols_lay.addWidget(self._build_right_col(), 2)

        outer.addWidget(cols, 1)

        # Auto-select first component
        first = self._input_panel.selected_component_id()
        if first:
            self._on_component_selected(first)

    def _build_right_col(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Run button
        self._run_btn = QPushButton("▶  진단 실행")
        self._run_btn.setStyleSheet(
            "QPushButton { background:#185FA5; color:#FFFFFF; border:none;"
            " border-radius:8px; padding:12px; font-size:14px; font-weight:700; }"
            "QPushButton:hover { background:#1472BA; }"
            "QPushButton:disabled { background:#B0BEC5; }"
        )
        self._run_btn.clicked.connect(self._on_run_diagnosis)
        lay.addWidget(self._run_btn)

        # Run all button
        run_all_btn = QPushButton("⚡  전체 부품 진단")
        run_all_btn.setStyleSheet(
            "QPushButton { background:#378ADD; color:#FFFFFF; border:none;"
            " border-radius:8px; padding:10px; font-size:12px; font-weight:600; }"
            "QPushButton:hover { background:#1472BA; }"
        )
        run_all_btn.clicked.connect(self._on_run_all)
        lay.addWidget(run_all_btn)

        # Reset button
        reset_btn = QPushButton("↺  초기화")
        reset_btn.setStyleSheet(
            "QPushButton { background:#FFFFFF; color:#667085; border:1px solid #D3D1C7;"
            " border-radius:8px; padding:10px; font-size:12px; }"
            "QPushButton:hover { background:#F4F3EF; }"
        )
        reset_btn.clicked.connect(self._on_reset)
        lay.addWidget(reset_btn)

        # Spec reference panel
        spec = QFrame()
        spec.setStyleSheet(
            "QFrame { background:#FFFFFF; border:1px solid #D3D1C7; border-radius:8px; }"
        )
        spec_lay = QVBoxLayout(spec)
        spec_lay.setContentsMargins(10, 8, 10, 8)
        spec_lay.setSpacing(4)
        spec_hdr = QLabel("정격 전압 참조")
        spec_hdr.setStyleSheet("font-size:11px; font-weight:700; color:#344054; border:none;")
        spec_lay.addWidget(spec_hdr)
        self._spec_label = QLabel("부품을 선택하세요")
        self._spec_label.setWordWrap(True)
        self._spec_label.setStyleSheet("font-size:11px; color:#344054; border:none; line-height:160%;")
        spec_lay.addWidget(self._spec_label)
        lay.addWidget(spec)

        # Simulation log
        log_lbl = QLabel("시뮬레이션 로그")
        log_lbl.setStyleSheet("font-size:11px; font-weight:700; color:#344054;")
        lay.addWidget(log_lbl)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 9))
        self._log.setStyleSheet(
            "QTextEdit { background:#0C2340; color:#A8C0D8;"
            " border:1px solid #1A3A5C; border-radius:6px; padding:6px; }"
        )
        lay.addWidget(self._log, 1)
        return w

    @Slot(str)
    def _on_component_selected(self, cid: str):
        comp = self._components.get(cid)
        if comp:
            self._spec_label.setText(
                f"모델: {comp.model_name}\n"
                f"정상:  {comp.voltage_warn_high:.2f} ~ {comp.voltage_max:.2f} V\n"
                f"경고:  {comp.voltage_min:.2f} ~ {comp.voltage_warn_high - 0.01:.2f} V\n"
                f"임계:  < {comp.voltage_min:.2f} V"
                + (f"  또는  > {comp.voltage_max:.2f} V" if comp.has_ov_critical else "")
            )

    @Slot(str)
    def _on_scenario_selected(self, scenario: str):
        self._current_scenario = scenario
        cid = self._input_panel.selected_component_id()
        if cid is None:
            self._log_op("⚠  부품을 먼저 선택하세요")
            return
        comp = self._components.get(cid)
        v = self._scenario_handler.get_voltage(scenario, comp)
        if v is not None:
            self._input_panel.set_voltage(v)
        self._on_run_diagnosis()

    @Slot()
    def _on_run_diagnosis(self):
        cid = self._input_panel.selected_component_id()
        if cid is None:
            self._log_op("⚠  부품을 먼저 선택하세요")
            return
        comp = self._components[cid]
        scenario = self._current_scenario
        voltage = self._input_panel.get_voltage()

        if scenario in ("NO_DATA", "SENSOR_ERROR"):
            voltage = None

        state, zone = self._comparator.compare(comp, voltage, scenario)
        severity = self._classifier.classify(state, zone)
        fault_code = self._fault_mapper.get_code(cid, state)
        maintenance = self._maint_mapper.get_action(fault_code, state)
        result = self._builder.build(comp, voltage, state, severity, fault_code, maintenance)

        dev_pct = (
            self._volt_handler.compute_deviation_pct(voltage, comp)
            if voltage is not None else None
        )
        self._inject_panel.update_preview(result, dev_pct)
        self._input_panel.update_result(result)

        log_line = self._msg_builder.build_terminal_log(result)
        print(log_line)
        self._log_op(log_line)

        self.diagnosis_done.emit(result)
        self._current_scenario = None

    @Slot()
    def _on_run_all(self):
        for comp in sorted(self._components.values(), key=lambda c: c.priority):
            mid = (comp.voltage_warn_high + comp.voltage_max) / 2
            state, zone = self._comparator.compare(comp, mid)
            severity = self._classifier.classify(state, zone)
            fault_code = self._fault_mapper.get_code(comp.id, state)
            maintenance = self._maint_mapper.get_action(fault_code, state)
            result = self._builder.build(comp, mid, state, severity, fault_code, maintenance)
            self._input_panel.update_result(result)
            self.diagnosis_done.emit(result)
            log_line = self._msg_builder.build_terminal_log(result)
            print(log_line)
            self._log_op(log_line)

    @Slot()
    def _on_reset(self):
        self._input_panel.reset()
        self._inject_panel.reset_preview()
        self._current_scenario = None
        self.reset_requested.emit()
        self._log_op("── 초기화 완료 ──")

    def _log_op(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{ts}] {message}")
