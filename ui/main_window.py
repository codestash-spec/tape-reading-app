from __future__ import annotations

import os
from typing import Callable, Optional

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets
from pyqtgraph.dockarea import DockArea, Dock

from ui.event_bridge import EventBridge
from ui.themes import Theme
from ui.themes import brand
from ui.widgets.dom_panel import DomPanel
from ui.widgets.delta_panel import DeltaPanel
from ui.widgets.footprint_panel import FootprintPanel
from ui.widgets.tape_panel import TapePanel
from ui.widgets.strategy_panel import StrategyPanel
from ui.widgets.execution_panel import ExecutionPanel
from ui.widgets.metrics_panel import MetricsPanel
from ui.widgets.logs_panel import LogsPanel
from ui.widgets.status_bar_widget import StatusBarWidget
from ui.widgets.order_ticket import OrderTicket
from ui.widgets.liquidity_map_panel import LiquidityMapPanel
from ui.widgets.volume_profile_panel import VolumeProfilePanel
from ui.widgets.heatmap_panel import HeatmapPanel
from ui.widgets.alerts_panel import AlertsPanel
from ui.widgets.regime_panel import RegimePanel
from ui.widgets.volatility_panel import VolatilityPanel
from ui.widgets.market_watch_panel import MarketWatchPanel
from ui.workspace_manager import WorkspaceManager
from ui.settings_window import SettingsWindow


class _ExecutionChart(QtWidgets.QWidget):
    def __init__(self, bridge: EventBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self.plot = pg.PlotWidget(background=brand.BG_DARK)
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.price_curve = self.plot.plot(pen=pg.mkPen(brand.ACCENT, width=2))
        self.fill_scatter = pg.ScatterPlotItem(symbol="o", size=8, brush=pg.mkBrush(brand.SUCCESS))
        self.plot.addItem(self.fill_scatter)
        self.ts: list[float] = []
        self.prices: list[float] = []
        self.fills: list[dict] = []

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.setLayout(layout)

        bridge.microstructureUpdated.connect(self.on_snapshot)
        bridge.orderStatusUpdated.connect(self.on_order)

    def on_snapshot(self, snap: dict) -> None:
        mid = snap.get("mid") or snap.get("price")
        if mid is None:
            return
        try:
            mid_f = float(mid)
        except Exception:
            return
        self.ts.append(len(self.ts))
        self.prices.append(mid_f)
        self.price_curve.setData(self.ts, self.prices)

    def on_order(self, evt: dict) -> None:
        if evt.get("status") not in ("fill", "partial_fill", "FILL", "PARTIAL"):
            return
        price = evt.get("avg_price") or evt.get("limit_price") or 0.0
        self.fills.append({"pos": (len(self.ts), price), "side": evt.get("side", "buy")})
        spots = [
            {
                "pos": f["pos"],
                "brush": pg.mkBrush(brand.SUCCESS if f["side"] == "buy" else brand.DANGER),
            }
            for f in self.fills
        ]
        self.fill_scatter.setData(spots)


class InstitutionalMainWindow(QtWidgets.QMainWindow):
    """
    Dockable institutional UI inspired by Bloomberg/Refinitiv/Bookmap layouts.
    """

    def __init__(
        self,
        bridge: EventBridge,
        theme_mode: str = "dark",
        mode: str = "sim",
        on_submit_order: Optional[Callable] = None,
        on_cancel_order: Optional[Callable[[str], None]] = None,
        provider_manager=None,
        event_bus=None,
        pm_settings: Optional[dict] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self.on_submit_order = on_submit_order
        self.on_cancel_order = on_cancel_order
        self.provider_manager = provider_manager
        self.bus = event_bus
        self.pm_settings = pm_settings or {}
        self.setWindowTitle("Bots Institucionais - Tape Reading")
        self.theme = Theme(theme_mode)
        self._apply_theme()

        self.settings = QtCore.QSettings("BotsInstitucionais", "InstitutionalUI")
        self._profile_key = f"profile/{os.getenv('PROFILE', 'default')}"
        self.workspace = WorkspaceManager(self, self.settings)

        self._load_qss(theme_mode)

        # Central chart
        self.chart = _ExecutionChart(bridge)
        self.area = DockArea()
        self.setCentralWidget(self.area)

        # Panels
        self.dom_panel = DomPanel()
        self.delta_panel = DeltaPanel()
        self.footprint_panel = FootprintPanel()
        self.tape_panel = TapePanel()
        self.strategy_panel = StrategyPanel()
        self.execution_panel = ExecutionPanel()
        self.metrics_panel = MetricsPanel()
        self.logs_panel = LogsPanel()
        self.liquidity_panel = LiquidityMapPanel()
        self.vol_profile_panel = VolumeProfilePanel()
        self.heatmap_panel = HeatmapPanel()
        self.alerts_panel = AlertsPanel()
        self.regime_panel = RegimePanel()
        self.vol_panel = VolatilityPanel()
        self.market_watch = MarketWatchPanel()
        self.market_watch.instrumentSelected.connect(self._switch_instrument)
        self.status_widget = StatusBarWidget()

        # Wire bridge
        self.dom_panel.connect_bridge(bridge)
        self.delta_panel.connect_bridge(bridge)
        self.footprint_panel.connect_bridge(bridge)
        self.tape_panel.connect_bridge(bridge)
        self.strategy_panel.connect_bridge(bridge)
        self.execution_panel.connect_bridge(bridge, on_cancel=self.on_cancel_order)
        self.metrics_panel.connect_bridge(bridge)
        self.logs_panel.connect_bridge(bridge)
        self.liquidity_panel.connect_bridge(bridge)
        self.vol_profile_panel.connect_bridge(bridge)
        self.regime_panel.connect_bridge(bridge)
        self.vol_panel.connect_bridge(bridge)
        self.market_watch.connect_bridge(bridge)
        self.status_widget.connect_bridge(bridge, mode=mode)

        # DockArea layout
        self.area.addDock(Dock("Chart", widget=self.chart))
        self.area.addDock(Dock("DOM", widget=self.dom_panel), "left", self.area.docks["Chart"])
        self.area.addDock(Dock("Delta", widget=self.delta_panel), "above", self.area.docks["DOM"])
        self.area.addDock(Dock("Footprint", widget=self.footprint_panel), "above", self.area.docks["Delta"])
        self.area.addDock(Dock("Tape", widget=self.tape_panel), "bottom", self.area.docks["Chart"])
        self.area.addDock(Dock("Strategy", widget=self.strategy_panel), "right", self.area.docks["Chart"])
        self.area.addDock(Dock("Execution", widget=self.execution_panel), "bottom", self.area.docks["Strategy"])
        self.area.addDock(Dock("Metrics", widget=self.metrics_panel), "bottom", self.area.docks["Execution"])
        self.area.addDock(Dock("Logs", widget=self.logs_panel), "bottom", self.area.docks["Tape"])
        self.area.addDock(Dock("Liquidity", widget=self.liquidity_panel), "right", self.area.docks["Execution"])
        self.area.addDock(Dock("VolumeProfile", widget=self.vol_profile_panel), "above", self.area.docks["Liquidity"])
        self.area.addDock(Dock("Regime", widget=self.regime_panel), "above", self.area.docks["VolumeProfile"])
        self.area.addDock(Dock("Volatility", widget=self.vol_panel), "above", self.area.docks["Regime"])
        self.area.addDock(Dock("MarketWatch", widget=self.market_watch), "left", self.area.docks["DOM"])

        self.statusBar().addPermanentWidget(self.status_widget)

        self._build_menu()
        self._build_toolbar()
        self.restore_state()

    def _apply_theme(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app:
            app.setPalette(self.theme.palette)
            app.setFont(self.theme.font)

    def _load_qss(self, mode: str) -> None:
        file = "ui/themes/institutional_dark.qss" if mode == "dark" else "ui/themes/institutional_light.qss"
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                QtWidgets.QApplication.instance().setStyleSheet(f.read())  # type: ignore

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
        for mode in ("live", "paper", "replay", "sim"):
            act = mode_menu.addAction(mode.title())
            act.setData(mode)
            act.triggered.connect(lambda checked=False, m=mode: self._on_mode_change(m))

        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)

    def _build_toolbar(self) -> None:
        toolbar = QtWidgets.QToolBar("Main")
        toolbar.setObjectName("Main")
        toolbar.setMovable(True)
        icon_path = "ui/themes/icons/"

        ticket_act = QtGui.QAction(QtGui.QIcon(icon_path + "ticket.svg"), "Order Ticket", self)
        ticket_act.triggered.connect(self._open_ticket)
        ws_act = QtGui.QAction(QtGui.QIcon(icon_path + "workspace.svg"), "Switch Workspace", self)
        ws_act.triggered.connect(self._load_workspace)
        reset_act = QtGui.QAction(QtGui.QIcon(icon_path + "reset.svg"), "Reset Layout", self)
        reset_act.triggered.connect(lambda: self.workspace.save_profile("default"))
        settings_act = QtGui.QAction(QtGui.QIcon(icon_path + "settings.svg"), "Settings", self)
        settings_act.triggered.connect(self._open_settings)
        help_act = QtGui.QAction(QtGui.QIcon(icon_path + "help.svg"), "About", self)
        help_act.triggered.connect(self._show_about)
        replay_act = QtGui.QAction(QtGui.QIcon(icon_path + "replay.svg"), "Replay Mode", self)
        replay_act.triggered.connect(lambda: self._on_mode_change("replay"))

        toolbar.addAction(ticket_act)
        toolbar.addAction(ws_act)
        toolbar.addAction(reset_act)
        toolbar.addSeparator()
        toolbar.addAction(replay_act)
        toolbar.addAction(settings_act)
        toolbar.addAction(help_act)

        self.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)
        # hotkeys
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self, activated=lambda: self._cycle_watch(-1))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self, activated=lambda: self._cycle_watch(1))

    def _on_mode_change(self, mode: str) -> None:
        self.status_widget.mode_label.setText(f"Mode: {mode}")

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "Bots Institucionais – UI\nPhases I–VII\nEvent-driven microstructure + execution stack.",
        )

    def _open_ticket(self) -> None:
        ticket = OrderTicket(on_submit=self.on_submit_order, on_cancel=self.on_cancel_order, parent=self)
        ticket.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        ticket.show()

    def _load_workspace(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(self, "Load workspace", "Profile name:", text="default")
        if ok and name:
            self.workspace.load_profile(name)

    def _open_settings(self) -> None:
        current = {
            "provider": self.provider_manager.active_name if self.provider_manager else None,
        }
        dlg = SettingsWindow(current, on_apply=self._apply_settings, parent=self)
        dlg.exec()

    def _apply_settings(self, cfg: dict) -> None:
        if self.provider_manager and cfg.get("provider"):
            self.provider_manager.start(cfg["provider"])
            self.status_widget.conn_label.setText(f"Conn: {cfg['provider']}")
            # reset event bridge subscriptions to avoid duplicates
            self.bridge.stop()
            self.bridge.start()

    def _cycle_watch(self, step: int) -> None:
        total = self.market_watch.table.rowCount()
        if total == 0:
            return
        row = self.market_watch.table.currentRow()
        if row < 0:
            row = 0
        next_row = max(0, min(total - 1, row + step))
        self.market_watch.table.selectRow(next_row)
        sym_item = self.market_watch.table.item(next_row, 0)
        if sym_item:
            self._switch_instrument(sym_item.text())

    def _switch_instrument(self, symbol: str) -> None:
        if not self.bus:
            return
        # rebuild provider manager with new symbol
        if self.provider_manager:
            self.provider_manager.stop()
        if hasattr(self.market_watch, "disconnect_bridge"):
            self.market_watch.disconnect_bridge()
        cfg = dict(self.pm_settings)
        cfg["market_symbol"] = symbol
        cfg["symbols"] = [symbol]
        from providers.provider_manager import ProviderManager
        self.provider_manager = ProviderManager(self.bus, cfg)
        self.provider_manager.auto_start()
        self.bridge.stop()
        self.bridge.start()
        if hasattr(self.market_watch, "connect_bridge"):
            self.market_watch.connect_bridge(self.bridge)
        self.status_widget.conn_label.setText(f"Conn: {self.provider_manager.active_name}")
        self.statusBar().showMessage(f"[MarketWatch] User selected {symbol} (provider={self.provider_manager.active_name})", 3000)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.save_state()
        super().closeEvent(event)

    def save_state(self) -> None:
        self.settings.beginGroup(self._profile_key)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()
        self.workspace.save_profile("last")

    def restore_state(self) -> None:
        self.settings.beginGroup(self._profile_key)
        geometry = self.settings.value("geometry")
        state = self.settings.value("state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        self.settings.endGroup()
        self.workspace.ensure_default()
