# Entry point: launches the dashboard and operator windows and connects their signals
import sys
import os
import signal

# Ensure the project root is on sys.path regardless of working directory
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from csc_06_dashboard_ui.dashboard_window import DashboardWindow
from csc_07_operator_control_ui.operator_window import OperatorWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DroneElecDiagnosis")
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Allow Ctrl+C in terminal to quit the Qt event loop
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    # Qt blocks Python signal handling while in the event loop, so we need a
    # timer to periodically yield control back to Python to check for signals
    sigint_timer = QTimer()
    sigint_timer.setInterval(200)
    sigint_timer.timeout.connect(lambda: None)
    sigint_timer.start()

    dashboard = DashboardWindow()
    operator = OperatorWindow()

    operator.diagnosis_done.connect(dashboard.on_diagnosis_done)
    operator.reset_requested.connect(dashboard.on_reset_requested)

    # Position windows: simulation UI on left, dashboard fills remaining space
    screen = app.primaryScreen().availableGeometry()
    op_w = operator.width()
    op_h = min(operator.height(), screen.height() - 40)
    operator.resize(op_w, op_h)
    dash_w = max(1280, min(screen.width() - op_w - 20, 1600))
    dashboard.resize(dash_w, min(900, screen.height() - 40))
    operator.move(screen.x(), screen.y())
    dashboard.move(screen.x() + op_w + 10, screen.y())

    dashboard.show()
    operator.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
