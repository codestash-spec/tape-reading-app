from __future__ import annotations

import os
from typing import Optional

from PySide6 import QtCore, QtWidgets

from ui.event_bridge import EventBridge
from ui.themes import Theme
from ui.widgets.dom_panel import DomPanel
from ui.widgets.delta_panel import DeltaPanel
from ui.widgets.footprint_panel import FootprintPanel
from ui.widgets.tape_panel import TapePanel
from ui.widgets.strategy_panel import StrategyPanel
from ui.widgets.execution_panel import ExecutionPanel
from ui.widgets.metrics_panel import MetricsPanel
from ui.widgets.logs_panel import LogsPanel
from ui.widgets.status_bar_widget import StatusBarWidget


class InstitutionalMainWindow(QtWidgets.QMainWindow):
    """
    Dockable institutional UI inspired by Bloomberg/Refinitiv/Bookmap layouts.
    """

    def __init__(self, bridge: EventBridge, theme_mode: str = "dark", mode: str = "sim", parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self.setWindowTitle("Bots Institucionais – Tape Reading")
        self.theme = Theme(theme_mode)
        self._apply_theme()

        self.settings = QtCore.QSettings("BotsInstitucionais", "InstitutionalUI")
        self._profile_key = f"profile/{os.getenv('PROFILE', 'default')}"

        # Central placeholder
        central_label = QtWidgets.QLabel("Microstructure View")
        central_label.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(central_label)

        # Panels
        self.dom_panel = DomPanel()
        self.delta_panel = DeltaPanel()
        self.footprint_panel = FootprintPanel()
        self.tape_panel = TapePanel()
        self.strategy_panel = StrategyPanel()
        self.execution_panel = ExecutionPanel()
        self.metrics_panel = MetricsPanel()
        self.logs_panel = LogsPanel()
        self.status_widget = StatusBarWidget()

        # Wire bridge
        self.dom_panel.connect_bridge(bridge)
        self.delta_panel.connect_bridge(bridge)
        self.footprint_panel.connect_bridge(bridge)
        self.tape_panel.connect_bridge(bridge)
        self.strategy_panel.connect_bridge(bridge)
        self.execution_panel.connect_bridge(bridge)
        self.metrics_panel.connect_bridge(bridge)
        self.logs_panel.connect_bridge(bridge)
        self.status_widget.connect_bridge(bridge, mode=mode)

        # Docks
        self._add_dock("DOM", self.dom_panel, QtCore.Qt.LeftDockWidgetArea)
        self._add_dock("Delta", self.delta_panel, QtCore.Qt.LeftDockWidgetArea)
        self._add_dock("Footprint", self.footprint_panel, QtCore.Qt.LeftDockWidgetArea)
        self._add_dock("Tape", self.tape_panel, QtCore.Qt.BottomDockWidgetArea)
        self._add_dock("Strategy", self.strategy_panel, QtCore.Qt.RightDockWidgetArea)
        self._add_dock("Execution", self.execution_panel, QtCore.Qt.RightDockWidgetArea)
        self._add_dock("Metrics", self.metrics_panel, QtCore.Qt.BottomDockWidgetArea)
        self._add_dock("Logs", self.logs_panel, QtCore.Qt.BottomDockWidgetArea)

        self.statusBar().addPermanentWidget(self.status_widget)

        self._build_menu()
        self.restore_state()

    def _apply_theme(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app:
            app.setPalette(self.theme.palette)
            app.setFont(self.theme.font)

    def _add_dock(self, title: str, widget: QtWidgets.QWidget, area: QtCore.Qt.DockWidgetArea) -> None:
        dock = QtWidgets.QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setObjectName(title)
        dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea
            | QtCore.Qt.RightDockWidgetArea
            | QtCore.Qt.TopDockWidgetArea
            | QtCore.Qt.BottomDockWidgetArea
        )
        self.addDockWidget(area, dock)

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.QApplication.instance().quit)

        view_menu = menubar.addMenu("&View")
        for dock in self.findChildren(QtWidgets.QDockWidget):
            action = dock.toggleViewAction()
            view_menu.addAction(action)

        mode_menu = menubar.addMenu("&Mode")
        for mode in ("live", "paper", "replay"):
            act = mode_menu.addAction(mode.title())
            act.setData(mode)
            act.triggered.connect(lambda checked=False, m=mode: self._on_mode_change(m))

        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)

    def _on_mode_change(self, mode: str) -> None:
        self.status_widget.mode_label.setText(f"Mode: {mode}")

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "Bots Institucionais – UI\nPhases I–VII\nEvent-driven microstructure + execution stack.",
        )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.save_state()
        super().closeEvent(event)

    def save_state(self) -> None:
        self.settings.beginGroup(self._profile_key)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()

    def restore_state(self) -> None:
        self.settings.beginGroup(self._profile_key)
        geometry = self.settings.value("geometry")
        state = self.settings.value("state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        self.settings.endGroup()

