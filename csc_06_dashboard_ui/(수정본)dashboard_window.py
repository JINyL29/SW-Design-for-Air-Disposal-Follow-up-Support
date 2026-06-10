# Main dashboard window with KPI cards, wiring scene, table, log, and fault detail panel
from typing import Dict, List, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QProgressBar, QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, Slot
from models.diagnosis_result import DiagnosisResult, VoltageState, Severity
from csc_01_component_db.csu_01_component_data_loader import get_component_loader
from csc_06_dashboard_ui.dashboard_wiring_scene import DashboardWiringWidget
from csc_06_dashboard_ui.dashboard_table_widget import DashboardTableWidget
from csc_06_dashboard_ui.dashboard_log_widget import DashboardLogWidget

_PIPELINE_STEPS = [
    "① 입력 수집",
    "② 전압 비교",
    "③ 상태 분류",
    "④ 코드 생성",
    "⑤ 정비 매핑",
    "⑥ 결과 출력",
]
_SEV_COLORS = {
    Severity.CRITICAL: "#E24B4A",
    Severity.HIGH:     "#BA7517",
    Severity.MEDIUM:   "#378ADD",
    Severity.LOW:      "#639922",
}


def _card(title: str, value: str, color: str = "#344054") -> QWidget:
    w = QFrame()
    w.setStyleSheet(
        "QFrame { background:#FFFFFF; border:1px solid #D3D1C7;"
        " border-radius:9px; padding:8px; }"
    )
    lay = QVBoxLayout(w)
    lay.setContentsMargins(10, 8, 10, 8)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setStyleSheet("font-size:10px; color:#667085; border:none;")
    v = QLabel(value)
    v.setObjectName("kpi_value")
    v.setStyleSheet(f"font-size:22px; font-weight:700; color:{color}; border:none;")
    lay.addWidget(t)
    lay.addWidget(v)
    return w


class DashboardWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loader = get_component_loader()
        self._components = {c.id: c for c in self._loader.get_all()}
        self._results: Dict[str, DiagnosisResult] = {}
        self._result_times: Dict[str, str] = {}
        self._active_filter: Optional[Severity] = None
        self.setWindowTitle("드론 전기 계통 진단 대시보드")
        self.setMinimumSize(1280, 720)
        self.resize(1600, 900)
        self._setup_ui()
        self._apply_global_style()

    def _apply_global_style(self):
        self.setStyleSheet(
            "QMainWindow, QWidget { background:#F4F3EF; font-family: 'Segoe UI', sans-serif; }"
            "QLabel { border:none; }"
        )

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        # Title bar with last diagnosis timestamp
        title_row = QWidget()
        title_row_lay = QHBoxLayout(title_row)
        title_row_lay.setContentsMargins(0, 0, 0, 0)
        title = QLabel("드론 전기 계통 고장 진단 시스템")
        title.setStyleSheet(
            "font-size:16px; font-weight:700; color:#1A2B3C;"
            " padding-bottom:4px; border-bottom:1px solid #D3D1C7;"
        )
        self._last_diag_lbl = QLabel("마지막 진단: —")
        self._last_diag_lbl.setStyleSheet(
            "font-size:10px; color:#667085; padding-bottom:4px;"
        )
        title_row_lay.addWidget(title)
        title_row_lay.addStretch()
        title_row_lay.addWidget(self._last_diag_lbl)
        outer.addWidget(title_row)

        # 3-column layout
        grid = QWidget()
        grid_lay = QHBoxLayout(grid)
        grid_lay.setSpacing(10)
        grid_lay.setContentsMargins(0, 0, 0, 0)

        grid_lay.addWidget(self._build_left_panel(), 0)
        grid_lay.addWidget(self._build_center_panel(), 1)
        grid_lay.addWidget(self._build_right_panel(), 0)

        outer.addWidget(grid, 1)

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(190)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._kpi_total  = _card("전체 부품", "8", "#344054")
        self._kpi_normal = _card("정상", "0", "#639922")
        self._kpi_warn   = _card("경고", "0", "#BA7517")
        for c in [self._kpi_total, self._kpi_normal, self._kpi_warn]:
            lay.addWidget(c)

        # System health gauge (replaces the removed fault count card)
        health_frame = QFrame()
        health_frame.setStyleSheet(
            "QFrame { background:#FFFFFF; border:1px solid #D3D1C7; border-radius:9px; }"
        )
        health_lay = QVBoxLayout(health_frame)
        health_lay.setContentsMargins(10, 8, 10, 8)
        health_lay.setSpacing(4)
        health_hdr = QLabel("시스템 건강도")
        health_hdr.setStyleSheet("font-size:10px; color:#667085; font-weight:600;")
        health_lay.addWidget(health_hdr)
        self._health_bar = QProgressBar()
        self._health_bar.setRange(0, 100)
        self._health_bar.setValue(0)
        self._health_bar.setTextVisible(True)
        self._health_bar.setFormat("%p%")
        self._health_bar.setFixedHeight(20)
        self._health_bar.setStyleSheet(
            "QProgressBar { background:#EAE9E3; border-radius:5px; color:#344054;"
            " font-size:10px; font-weight:600; }"
            "QProgressBar::chunk { background:#639922; border-radius:5px; }"
        )
        health_lay.addWidget(self._health_bar)
        lay.addWidget(health_frame)

        # Severity distribution
        sev_frame = QFrame()
        sev_frame.setStyleSheet(
            "QFrame { background:#FFFFFF; border:1px solid #D3D1C7; border-radius:9px; }"
        )
        sev_lay = QVBoxLayout(sev_frame)
        sev_lay.setContentsMargins(10, 8, 10, 8)
        sev_lay.setSpacing(4)
        sev_hdr = QLabel("심각도 분포")
        sev_hdr.setStyleSheet("font-size:10px; color:#667085; font-weight:600;")
        sev_lay.addWidget(sev_hdr)
        self._sev_bars: Dict[Severity, QProgressBar] = {}
        for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(4)
            lbl = QLabel(sev.value)
            lbl.setFixedWidth(58)
            lbl.setStyleSheet(f"font-size:9px; color:{_SEV_COLORS[sev]};")
            bar = QProgressBar()
            bar.setRange(0, len(self._components))
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet(
                f"QProgressBar {{ background:#EAE9E3; border-radius:5px; }}"
                f"QProgressBar::chunk {{ background:{_SEV_COLORS[sev]}; border-radius:5px; }}"
            )
            self._sev_bars[sev] = bar
            row_l.addWidget(lbl)
            row_l.addWidget(bar)
            sev_lay.addWidget(row_w)
        lay.addWidget(sev_frame)

        # Pipeline miniview
        pipe_frame = QFrame()
        pipe_frame.setStyleSheet(
            "QFrame { background:#FFFFFF; border:1px solid #D3D1C7; border-radius:9px; }"
        )
        pipe_lay = QVBoxLayout(pipe_frame)
        pipe_lay.setContentsMargins(10, 8, 10, 8)
        pipe_lay.setSpacing(3)
        hdr2 = QLabel("진단 파이프라인")
        hdr2.setStyleSheet("font-size:10px; color:#667085; font-weight:600;")
        pipe_lay.addWidget(hdr2)
        _pipe_style = ("font-size:9px; color:#667085; background:#F4F3EF;"
                       " border-radius:4px; padding:3px 6px;")
        self._pipe_labels: List[QLabel] = []
        for step in _PIPELINE_STEPS:
            lbl = QLabel(step)
            lbl.setStyleSheet(_pipe_style)
            pipe_lay.addWidget(lbl)
            self._pipe_labels.append(lbl)
        lay.addWidget(pipe_frame)
        lay.addStretch()
        return w

    # ── Center panel ─────────────────────────────────────────────────────────
    def _build_center_panel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._wiring = DashboardWiringWidget()
        lay.addWidget(self._wiring, 3)

        self._table = DashboardTableWidget(list(self._components.values()))
        lay.addWidget(self._table, 2)

        self._log = DashboardLogWidget()
        self._log.setMinimumHeight(110)
        lay.addWidget(self._log, 1)
        return w

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_right_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(300)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        hdr = QLabel("활성 고장 상세 정보")
        hdr.setStyleSheet("font-size:13px; font-weight:700; color:#344054;")
        lay.addWidget(hdr)

        # Severity filter buttons
        filter_row = QWidget()
        filter_lay = QHBoxLayout(filter_row)
        filter_lay.setContentsMargins(0, 2, 0, 2)
        filter_lay.setSpacing(4)
        self._filter_btns: Dict = {}
        filter_defs = [
            (None,              "전체",  "#344054"),
            (Severity.CRITICAL, "긴급",  "#E24B4A"),
            (Severity.HIGH,     "높음",  "#BA7517"),
            (Severity.MEDIUM,   "중간",  "#378ADD"),
        ]
        for sev, label, color in filter_defs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(sev is None)
            btn.setStyleSheet(
                f"QPushButton {{ background:#FFFFFF; color:{color}; border:1px solid {color};"
                f" border-radius:6px; padding:3px 6px; font-size:10px; font-weight:600; }}"
                f"QPushButton:checked {{ background:{color}; color:#FFFFFF; }}"
                f"QPushButton:hover {{ background:{color}; color:#FFFFFF; }}"
            )
            btn.clicked.connect(lambda _=False, s=sev: self._on_filter_clicked(s))
            filter_lay.addWidget(btn)
            self._filter_btns[sev] = btn
        lay.addWidget(filter_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border:1px solid #D3D1C7; border-radius:9px; background:#FFFFFF; }"
        )
        self._fault_detail_container = QWidget()
        self._fault_detail_layout = QVBoxLayout(self._fault_detail_container)
        self._fault_detail_layout.setContentsMargins(8, 8, 8, 8)
        self._fault_detail_layout.setSpacing(8)
        self._fault_detail_layout.addStretch()
        scroll.setWidget(self._fault_detail_container)
        lay.addWidget(scroll, 1)
        return w

    def _on_filter_clicked(self, severity: Optional[Severity]):
        self._active_filter = severity
        for sev, btn in self._filter_btns.items():
            btn.setChecked(sev is severity)
        self._refresh_fault_detail()

    def _make_fault_card(self, result: DiagnosisResult) -> QFrame:
        comp = self._components.get(result.component_id)
        comp_name = comp.name if comp else result.component_id
        sc = _SEV_COLORS.get(result.severity, "#888")
        ts = self._result_times.get(result.component_id, "")

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:#FFF; border:1.5px solid {sc}; border-radius:8px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setSpacing(4)
        lay.setContentsMargins(10, 8, 10, 10)

        volt_str = f"{result.current_voltage:.2f}V" if result.current_voltage is not None else "N/A"

        top = QLabel(f"▸ {comp_name}")
        top.setStyleSheet(f"font-weight:700; font-size:14px; color:{sc};")
        top.setWordWrap(True)

        code_row = QLabel(f"코드: {result.fault_code or '?'}  |  측정값: {volt_str}")
        code_row.setStyleSheet(f"font-size:11px; color:{sc}; font-weight:600;")

        info = QLabel(f"상태: {result.state.value}  |  심각도: {result.severity.value}")
        info.setStyleSheet("font-size:11px; color:#667085;")
        info.setWordWrap(True)

        lay.addWidget(top)
        lay.addWidget(code_row)
        lay.addWidget(info)

        if ts:
            time_lbl = QLabel(f"감지 시각: {ts}")
            time_lbl.setStyleSheet("font-size:10px; color:#9AA5B4;")
            lay.addWidget(time_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{sc}; max-height:1px; border:none;")
        lay.addWidget(sep)

        hdr = QLabel("정비 절차")
        hdr.setStyleSheet("font-size:12px; font-weight:700; color:#344054;")
        lay.addWidget(hdr)

        maint = QLabel(result.maintenance_action)
        maint.setWordWrap(True)
        maint.setStyleSheet("font-size:12px; color:#344054;")
        maint.setMinimumHeight(36)
        lay.addWidget(maint)

        return card

    def _refresh_fault_detail(self):
        while self._fault_detail_layout.count() > 1:
            item = self._fault_detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        faults = [r for r in self._results.values() if r.is_fault]
        if self._active_filter is not None:
            faults = [r for r in faults if r.severity == self._active_filter]
        faults.sort(key=lambda r: list(Severity).index(r.severity), reverse=True)

        for result in faults:
            card = self._make_fault_card(result)
            self._fault_detail_layout.insertWidget(
                self._fault_detail_layout.count() - 1, card
            )

        if not faults:
            msg = "활성 고장 없음 ✓" if self._active_filter is None else "해당 심각도 고장 없음"
            no_fault = QLabel(msg)
            no_fault.setStyleSheet("font-size:12px; color:#639922; padding:12px;")
            self._fault_detail_layout.insertWidget(0, no_fault)

    def _kpi_val(self, card) -> QLabel:
        return card.findChild(QLabel, "kpi_value")

    def _refresh_kpi(self):
        rv = list(self._results.values())
        total  = len(self._components)
        normal = sum(1 for r in rv if r.state == VoltageState.NORMAL)
        warn   = sum(1 for r in rv if r.state == VoltageState.UNDER_VOLTAGE and r.severity == Severity.HIGH)
        for card, val in zip(
            [self._kpi_total, self._kpi_normal, self._kpi_warn],
            [total, normal, warn],
        ):
            self._kpi_val(card).setText(str(val))

        # Health percentage bar
        health_pct = int(normal / total * 100) if total > 0 and len(rv) > 0 else 0
        self._health_bar.setValue(health_pct)
        chunk_color = "#639922" if health_pct >= 80 else ("#BA7517" if health_pct >= 50 else "#E24B4A")
        self._health_bar.setStyleSheet(
            "QProgressBar { background:#EAE9E3; border-radius:5px; color:#344054;"
            " font-size:10px; font-weight:600; }"
            f"QProgressBar::chunk {{ background:{chunk_color}; border-radius:5px; }}"
        )

        counts = {s: 0 for s in Severity}
        for r in self._results.values():
            counts[r.severity] = counts.get(r.severity, 0) + 1
        for sev, bar in self._sev_bars.items():
            bar.setValue(counts.get(sev, 0))

    def _flash_pipeline(self):
        _on  = "font-size:9px;color:#FFFFFF;background:#378ADD;border-radius:4px;padding:3px 6px;"
        _off = "font-size:9px;color:#667085;background:#F4F3EF;border-radius:4px;padding:3px 6px;"
        for lbl in self._pipe_labels:
            lbl.setStyleSheet(_on)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(600, lambda: [lbl.setStyleSheet(_off) for lbl in self._pipe_labels])

    # ── Slots ─────────────────────────────────────────────────────────────────
    @Slot(object)
    def on_diagnosis_done(self, result: DiagnosisResult):
        self._results[result.component_id] = result
        if result.is_fault:
            self._result_times[result.component_id] = datetime.now().strftime("%H:%M:%S")
        ts_now = datetime.now().strftime("%H:%M:%S")
        self._last_diag_lbl.setText(f"마지막 진단: {ts_now}  —  {result.component_id}")
        self._wiring.update_node(result)
        self._table.update_result(result)
        self._log.append_result(result)
        self._refresh_kpi()
        self._refresh_fault_detail()
        self._flash_pipeline()

    @Slot(str)
    def on_impact_message(self, message: str):
        """연쇄 영향 메시지를 로그 패널에 별도 색상으로 출력"""
        if message:
            self._log.append_impact(message)

    @Slot()
    def on_reset_requested(self):
        self._results.clear()
        self._result_times.clear()
        self._last_diag_lbl.setText("마지막 진단: —")
        self._wiring.reset()
        self._table.reset()
        self._log.append_info("── 전체 초기화 완료 ──")
        self._refresh_kpi()
        self._refresh_fault_detail()