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

# 실제 부품 간 직접 전력 공급 관계 (PDB는 별도 부품 없음)
_DOWNSTREAM = {
    "BAT": ["ESC", "BEC"],
    "ESC": ["MOT"],
    "BEC": ["FC", "TEL", "CAM"],
    "FC":  ["GPS"],
}


class OperatorWindow(QMainWindow):
    diagnosis_done = Signal(object)   # DiagnosisResult
    reset_requested = Signal()
    impact_message = Signal(str)      # 연쇄 영향 메시지
    wire_warning   = Signal(object)   # list of wire warning dicts

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
        self._last_diag: dict = {}        # {comp_id: {"voltage": v, "scenario": s, ...}}
        self._fault_streak: dict = {}     # {comp_id: consecutive fault count}

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
        zone_sev = self._classifier.classify(state, zone)
        fault_code = self._fault_mapper.get_code(cid, state)
        fc_obj = self._fault_mapper.get_fault_code_obj(fault_code) if fault_code else None
        severity = self._classifier.resolve(zone_sev, fc_obj.severity if fc_obj else None, zone)
        maintenance = self._maint_mapper.get_action(fault_code, state)
        result = self._builder.build(comp, voltage, state, severity, fault_code, maintenance)

        dev_pct = (
            self._volt_handler.compute_deviation_pct(voltage, comp)
            if voltage is not None else None
        )
        self._inject_panel.update_preview(result, dev_pct, fc_obj)
        self._input_panel.update_result(result)

        log_line = self._msg_builder.build_terminal_log(result)
        print(log_line)
        self._log_op(log_line)

        # source="manual" 로 기록 — 수동 주입 여부를 추적하기 위함
        self._last_diag[cid] = {
            "voltage": voltage, "scenario": scenario,
            "source": "manual", "state": result.state,
        }

        self.diagnosis_done.emit(result)

        impact_msg = self._msg_builder.build_impact_message(result)
        if impact_msg:
            self.impact_message.emit(impact_msg)

        # 하위 노드 연계 재진단
        if result.state == VoltageState.NORMAL:
            self._propagate_normal(cid)
        else:
            self._propagate_fault(cid, result.state)

        self._current_scenario = None

    def _propagate_normal(self, parent_id: str):
        """부모가 NORMAL → 하위 노드를 _last_diag 값으로 재진단.

        cascade 부품은 _last_diag에 정상 mid 전압이 저장되어 있으므로 → NORMAL 복귀
        수동 주입 고장 부품은 _last_diag에 고장 전압이 저장되어 있으므로 → FAULT 유지
        """
        from PySide6.QtCore import QTimer
        downstream = _DOWNSTREAM.get(parent_id, [])
        for i, child_id in enumerate(downstream):
            comp = self._components.get(child_id)
            if comp is None:
                continue
            saved = self._last_diag.get(child_id)
            if saved is None:
                # 한 번도 독립 진단된 적 없음 → 건강한 부품으로 간주
                voltage = round((comp.voltage_warn_high + comp.voltage_max) / 2, 2)
                scenario_key = None
            else:
                voltage = saved["voltage"]
                scenario_key = saved["scenario"]
            QTimer.singleShot(
                (i + 1) * 300,
                lambda c=comp, v=voltage, s=scenario_key, cid=child_id:
                    self._run_and_propagate(c, v, s, cid)
            )

    def _propagate_fault(self, parent_id: str, parent_state: VoltageState):
        """부모가 FAULT → 하위 노드에 연쇄 고장 전파.

        _last_diag는 수정하지 않는다.
        _last_diag는 '부모가 정상일 때의 고유 건강 전압'만 저장하므로,
        부모 고장으로 인한 cascade 진단은 덮어쓰면 안 됨.
        """
        from PySide6.QtCore import QTimer
        from csc_07_operator_control_ui.scenario_engine import _uv, _ov

        downstream = _DOWNSTREAM.get(parent_id, [])
        for i, child_id in enumerate(downstream):
            comp = self._components.get(child_id)
            if comp is None:
                continue

            if parent_state == VoltageState.UNDER_VOLTAGE:
                voltage = _uv(child_id)
                scenario_key = "UNDER_VOLTAGE"
            elif parent_state == VoltageState.OVER_VOLTAGE:
                voltage = _ov(child_id)
                scenario_key = "OVER_VOLTAGE"
            else:  # RAPID_DROP, SENSOR_ERROR, NO_DATA
                voltage = None
                scenario_key = "NO_DATA"

            QTimer.singleShot(
                (i + 1) * 300,
                lambda c=comp, v=voltage, s=scenario_key, cid=child_id:
                    self._run_and_propagate(c, v, s, cid, save_to_last_diag=False)
            )

    def _run_and_propagate(self, comp, voltage: Optional[float],
                           scenario_key: Optional[str], comp_id: str,
                           save_to_last_diag: bool = True):
        """재진단 실행 후 결과에 따라 하위 노드로 전파.

        save_to_last_diag=False: _propagate_fault에서 호출 시 _last_diag 불변 유지.
        """
        if scenario_key in ("NO_DATA", "SENSOR_ERROR"):
            voltage = None

        state, zone = self._comparator.compare(comp, voltage, scenario_key)
        zone_sev = self._classifier.classify(state, zone)
        fault_code = self._fault_mapper.get_code(comp.id, state)
        fc_obj = self._fault_mapper.get_fault_code_obj(fault_code) if fault_code else None
        severity = self._classifier.resolve(zone_sev, fc_obj.severity if fc_obj else None, zone)
        maintenance = self._maint_mapper.get_action(fault_code, state)
        result = self._builder.build(comp, voltage, state, severity, fault_code, maintenance)

        dev_pct = (
            self._volt_handler.compute_deviation_pct(voltage, comp)
            if voltage is not None else None
        )
        self._inject_panel.update_preview(result, dev_pct, fc_obj)
        self._input_panel.update_result(result)
        if save_to_last_diag:
            self._last_diag[comp_id] = {
                "voltage": voltage, "scenario": scenario_key,
                "source": "cascade", "state": result.state,
            }

        self.diagnosis_done.emit(result)
        impact_msg = self._msg_builder.build_impact_message(result)
        if impact_msg:
            self.impact_message.emit(impact_msg)
        log_line = self._msg_builder.build_terminal_log(result)
        print(log_line)
        self._log_op(f"  └─ 연계 재진단: {log_line}")

        # 결과에 따라 하위 노드 추가 전파
        if result.state == VoltageState.NORMAL:
            self._propagate_normal(comp_id)
        else:
            self._propagate_fault(comp_id, result.state)

    @Slot()
    def _on_run_all(self):
        from csc_07_operator_control_ui.scenario_engine import get_random_scenario
        from PySide6.QtCore import QTimer

        scenario = get_random_scenario()
        self._log_op(f"━━ 시나리오 #{scenario['id']}: {scenario['name']} ━━")
        self._log_op(f"   {scenario['description']}")

        faults = scenario["faults"]
        cascade_order = scenario["cascade_order"]

        # root cause 판별: 다른 고장 부품의 하위 노드가 아닌 경우
        def _is_root(cid):
            for parent, children in _DOWNSTREAM.items():
                if parent in faults and cid in children:
                    return False
            return True

        # Normal components → diagnose immediately (delay=0)
        for comp in self._components.values():
            if comp.id not in faults:
                mid = (comp.voltage_warn_high + comp.voltage_max) / 2
                QTimer.singleShot(
                    0, lambda c=comp, v=mid: self._run_single(c, v, None, True)
                )

        # Faulty components → cascade with 500ms per step
        for delay_idx, cid in enumerate(cascade_order):
            comp = self._components.get(cid)
            if comp is None or cid not in faults:
                continue
            scenario_key, volt_fn = faults[cid]
            voltage = volt_fn() if volt_fn is not None else None
            root = _is_root(cid)
            QTimer.singleShot(
                delay_idx * 500,
                lambda c=comp, v=voltage, s=scenario_key, r=root:
                    self._run_single(c, v, s, r),
            )

        # 모든 cascade 완료 후 연속 고장 체크
        check_delay = len(cascade_order) * 500 + 700
        faults_snapshot = set(faults.keys())
        QTimer.singleShot(check_delay,
                          lambda: self._check_wire_warnings(faults_snapshot))

    def _check_wire_warnings(self, faulted_ids: set):
        """연속 고장 횟수를 갱신하고 3회 이상인 부품에 전선 점검 경고를 발송."""
        for comp_id in self._components:
            if comp_id in faulted_ids:
                self._fault_streak[comp_id] = self._fault_streak.get(comp_id, 0) + 1
            else:
                self._fault_streak[comp_id] = 0

        all_fc = self._fault_mapper.get_all()
        warnings = []
        for comp_id, streak in self._fault_streak.items():
            if streak >= 3:
                comp = self._components.get(comp_id)
                comp_name = comp.name if comp else comp_id
                fc_obj = next(
                    (fc for fc in all_fc.values() if fc.component_id == comp_id), None
                )
                warnings.append({
                    "comp_id":      comp_id,
                    "comp_name":    comp_name,
                    "streak":       streak,
                    "awg":          fc_obj.awg if fc_obj else "",
                    "connector":    fc_obj.connector if fc_obj else "",
                    "rated_current": fc_obj.connector_rated_current if fc_obj else "",
                })

        if warnings:
            self.wire_warning.emit(warnings)

    def _run_single(self, comp, voltage: Optional[float], scenario_key: Optional[str],
                    is_root_cause: bool = True):
        """시나리오 진단 실행.

        is_root_cause=True  → 부품 자체 고장: _last_diag에 고장 전압 저장
        is_root_cause=False → cascade 고장: _last_diag에 정상 mid 전압 저장
                              (부모가 고쳐지면 자연스럽게 NORMAL로 복귀하기 위함)
        """
        if scenario_key in ("NO_DATA", "SENSOR_ERROR"):
            voltage = None

        state, zone = self._comparator.compare(comp, voltage, scenario_key)
        zone_sev = self._classifier.classify(state, zone)
        fault_code = self._fault_mapper.get_code(comp.id, state)
        fc_obj = self._fault_mapper.get_fault_code_obj(fault_code) if fault_code else None
        severity = self._classifier.resolve(zone_sev, fc_obj.severity if fc_obj else None, zone)
        maintenance = self._maint_mapper.get_action(fault_code, state)
        result = self._builder.build(comp, voltage, state, severity, fault_code, maintenance)

        dev_pct = (
            self._volt_handler.compute_deviation_pct(voltage, comp)
            if voltage is not None else None
        )
        self._inject_panel.update_preview(result, dev_pct, fc_obj)
        self._input_panel.update_result(result)

        # cascade 부품은 정상 mid 전압을 저장 → 부모 정상화 시 자연스럽게 NORMAL 복귀
        if is_root_cause:
            stored_v = voltage
            stored_s = scenario_key
        else:
            stored_v = round((comp.voltage_warn_high + comp.voltage_max) / 2, 2)
            stored_s = None

        self._last_diag[comp.id] = {
            "voltage": stored_v, "scenario": stored_s,
            "source": "cascade", "state": result.state,
        }

        self.diagnosis_done.emit(result)
        impact_msg = self._msg_builder.build_impact_message(result)
        if impact_msg:
            self.impact_message.emit(impact_msg)
        log_line = self._msg_builder.build_terminal_log(result)
        print(log_line)
        self._log_op(log_line)

    @Slot()
    def _on_reset(self):
        self._input_panel.reset()
        self._inject_panel.reset_preview()
        self._current_scenario = None
        self._last_diag.clear()
        self._fault_streak.clear()
        self.reset_requested.emit()
        self._log_op("── 초기화 완료 ──")

    def _log_op(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{ts}] {message}")