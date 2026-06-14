# QGraphicsScene-based drone electrical topology with state-driven node coloring
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsView, QWidget, QVBoxLayout, QLabel,
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath
from models.diagnosis_result import DiagnosisResult, VoltageState

# ── Node layout constants (center x, y) ──────────────────────────────────────
NODE_POS: Dict[str, tuple] = {
    "BAT": (90,  240),
    "PDB": (270, 240),
    "ESC": (450, 130),
    "MOT": (650,  70),
    "BEC": (450, 340),
    "FC":  (650, 250),
    "GPS": (830, 160),
    "TEL": (830, 320),
    "CAM": (650, 420),
}
NODE_W, NODE_H = 100, 52

# ── Edge definitions (from, to, line_type, dashed) ───────────────────────────
EDGES = [
    ("BAT", "PDB", "main_power",    False),
    ("PDB", "ESC", "main_power",    False),
    ("PDB", "BEC", "main_power",    False),
    ("ESC", "MOT", "pwm",           True),
    ("BEC", "FC",  "bec_12v",       False),
    ("BEC", "TEL", "bec_12v",       False),
    ("BEC", "CAM", "bec_12v",       False),
    ("FC",  "GPS", "v5_regulated",  False),
    ("FC",  "TEL", "uart",          True),
    ("FC",  "ESC", "pwm",           True),
]
EDGE_COLORS = {
    "main_power":   "#E24B4A",
    "bec_12v":      "#7F77DD",
    "v5_regulated": "#712B13",
    "uart":         "#1D9E75",
    "pwm":          "#5F5E5A",
}

# ── Node state styling ────────────────────────────────────────────────────────
_NODE_STYLE: Dict[str, tuple] = {
    "normal":  ("#EAF3DE", "#639922"),
    "uv":      ("#FAEEDA", "#BA7517"),
    "ov":      ("#FCEBEB", "#E24B4A"),
    "warning": ("#FAEEDA", "#BA7517"),
    "nodata":  ("#FBEAF0", "#D4537E"),
    "default": ("#F4F3EF", "#B0AFA8"),
}


def _state_style(state: Optional[VoltageState]) -> tuple:
    if state is None:
        return _NODE_STYLE["nodata"]
    if state == VoltageState.NORMAL:
        return _NODE_STYLE["normal"]
    if state == VoltageState.UNDER_VOLTAGE:
        return _NODE_STYLE["uv"]
    if state == VoltageState.OVER_VOLTAGE:
        return _NODE_STYLE["ov"]
    return _NODE_STYLE["warning"]


class NodeItem(QGraphicsRectItem):
    def __init__(self, node_id: str, label: str):
        cx, cy = NODE_POS[node_id]
        super().__init__(cx - NODE_W / 2, cy - NODE_H / 2, NODE_W, NODE_H)
        self.node_id = node_id
        self._label = label
        self._text = QGraphicsTextItem(label, self)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        self._text.setFont(font)
        self._center_text()
        self._badge: Optional[QGraphicsEllipseItem] = None
        if node_id == "PDB":
            self.set_state_default()
        else:
            self.set_state(None)
        self.setZValue(2)

    def _center_text(self):
        br = self._text.boundingRect()
        r = self.rect()
        self._text.setPos(
            r.x() + (r.width() - br.width()) / 2,
            r.y() + (r.height() - br.height()) / 2,
        )

    def set_state_default(self):
        """진단 없이 회색(기본) 상태로 표시 — PDB 전용."""
        bg, border = _NODE_STYLE["default"]
        self.setBrush(QBrush(QColor(bg)))
        self.setPen(QPen(QColor(border), 1.8))
        self._text.setDefaultTextColor(QColor("#1A1A1A"))
        if self._badge:
            self._badge.setVisible(False)

    def set_state(self, state: Optional[VoltageState], voltage: Optional[float] = None):
        bg, border = _state_style(state)
        self.setBrush(QBrush(QColor(bg)))
        self.setPen(QPen(QColor(border), 1.8))
        self._text.setDefaultTextColor(QColor("#1A1A1A"))
        self._update_badge(state)

    def _update_badge(self, state: Optional[VoltageState]):
        if self._badge:
            self._badge.setVisible(False)
        is_fault = state not in (None, VoltageState.NORMAL, VoltageState.NO_DATA)
        if not is_fault:
            return
        if self._badge is None:
            self._badge = QGraphicsEllipseItem(-9, -9, 18, 18, self)
            badge_text = QGraphicsTextItem("!", self._badge)
            badge_font = QFont()
            badge_font.setPointSize(7)
            badge_font.setBold(True)
            badge_text.setFont(badge_font)
            badge_text.setDefaultTextColor(QColor("#FFFFFF"))
            badge_text.setPos(-4, -8)
            self._badge.setZValue(10)
        r = self.rect()
        self._badge.setPos(r.x() + r.width() - 6, r.y() - 3)
        color = "#E24B4A" if state == VoltageState.OVER_VOLTAGE else "#BA7517"
        self._badge.setBrush(QBrush(QColor(color)))
        self._badge.setPen(QPen(QColor("#FFFFFF"), 1))
        self._badge.setVisible(True)


class WiringScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 960, 490)
        self._nodes: Dict[str, NodeItem] = {}
        self._build_scene()

    def _build_scene(self):
        self.setBackgroundBrush(QBrush(QColor("#FAFAF8")))
        self._draw_edges()
        node_labels = {
            "BAT": "Battery", "PDB": "PDB", "ESC": "ESC",
            "MOT": "Motor",   "BEC": "BEC", "FC":  "FC",
            "GPS": "GPS",     "TEL": "Telemetry", "CAM": "CAM",
        }
        for nid, label in node_labels.items():
            node = NodeItem(nid, label)
            self.addItem(node)
            self._nodes[nid] = node

    def _draw_edges(self):
        for src, dst, line_type, dashed in EDGES:
            sx, sy = NODE_POS[src]
            dx, dy = NODE_POS[dst]
            color = EDGE_COLORS.get(line_type, "#888888")
            pen = QPen(QColor(color), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            if dashed:
                pen.setStyle(Qt.PenStyle.DashLine)
            line = QGraphicsLineItem(sx, sy, dx, dy)
            line.setPen(pen)
            line.setZValue(1)
            self.addItem(line)

    def update_node(self, result: DiagnosisResult):
        node = self._nodes.get(result.component_id)
        if node:
            node.set_state(result.state, result.current_voltage)
        # PDB는 독립 부품이 없으므로 BAT 상태를 그대로 따라감
        if result.component_id == "BAT":
            pdb_node = self._nodes.get("PDB")
            if pdb_node:
                pdb_node.set_state(result.state, result.current_voltage)

    def reset_nodes(self):
        for nid, node in self._nodes.items():
            # PDB는 진단 대상이 아니므로 기본(회색) 상태로 초기화
            if nid == "PDB":
                node.set_state_default()
            else:
                node.set_state(None)


class DashboardWiringWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("전기 배선도 토폴로지")
        header.setStyleSheet("font-weight:600; font-size:12px; color:#344054;")
        layout.addWidget(header)

        self._scene = WiringScene()
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setStyleSheet(
            "QGraphicsView { border:1px solid #D3D1C7; border-radius:6px; background:#FAFAF8; }"
        )
        self._view.setMinimumHeight(240)
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        layout.addWidget(self._view)

        self._add_legend(layout)

    def _add_legend(self, parent_layout):
        legend_row = QWidget()
        row_layout = QVBoxLayout(legend_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(2)
        entries = [
            ("#E24B4A", "44V 메인파워"),
            ("#7F77DD", "12V BEC출력"),
            ("#712B13", "5V 조정전압"),
            ("#1D9E75", "UART 신호 (점선)"),
            ("#5F5E5A", "PWM 신호 (점선)"),
        ]
        from PySide6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.setSpacing(12)
        for color, label in entries:
            item = QLabel(f"─ {label}")
            item.setStyleSheet(f"color:{color}; font-size:9px;")
            h.addWidget(item)
        h.addStretch()
        row_layout.addLayout(h)
        parent_layout.addWidget(legend_row)

    def update_node(self, result: DiagnosisResult):
        self._scene.update_node(result)

    def reset(self):
        self._scene.reset_nodes()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
