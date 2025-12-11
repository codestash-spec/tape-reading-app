from __future__ import annotations

import os
import time
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
from ui.widgets.provider_debug_panel import ProviderDebugPanel
from ui.widgets.market_watch_panel import MarketWatchPanel
from ui.workspace_manager import WorkspaceManager
from ui.settings_window import SettingsWindow
from ui import helpers


class CandlestickItem(pg.GraphicsObject):
    """
    Lightweight candlestick renderer adapted from pyqtgraph examples.
    """

    def __init__(self) -> None:
        super().__init__()
        self.data = []
        self.picture = None

    def setData(self, data) -> None:
        self.data = data
        self.picture = None
        self.update()

    def paint(self, p: QtGui.QPainter, *args) -> None:  # type: ignore[override]
        if self.picture is None:
            self.picture = QtGui.QPicture()
            painter = QtGui.QPainter(self.picture)
            for (x, open_, high, low, close) in self.data:
                bullish = close >= open_
                pen = pg.mkPen("#12d8fa" if bullish else "#ff5f56")
                brush = pg.mkBrush("#12d8fa" if bullish else "#ff5f56")
                painter.setPen(pen)
                # wick
                painter.drawLine(QtCore.QPointF(x, low), QtCore.QPointF(x, high))
                # body
                top = open_ if bullish else close
                height = abs(close - open_)
                rect = QtCore.QRectF(x - 0.3, top, 0.6, height if height > 0 else 0.01)
                painter.fillRect(rect, brush)
                painter.drawRect(rect)
            painter.end()
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self) -> QtCore.QRectF:  # type: ignore[override]
        return QtCore.QRectF()


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.times = []

    def set_times(self, times):
        self.times = times or []

    def tickStrings(self, values, scale, spacing):
        out = []
        for v in values:
            if not self.times:
                out.append("")
                continue
            # map to closest time
            closest = min(self.times, key=lambda t: abs(t - v)) if self.times else v
            ts = time.strftime("%H:%M:%S", time.localtime(closest))
            out.append(ts)
        return out


class _ExecutionChart(QtWidgets.QWidget):
    def __init__(self, bridge: EventBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self.time_axis = TimeAxisItem(orientation="bottom")
        self.plot = pg.PlotWidget(background=brand.BG_DARK, axisItems={"bottom": self.time_axis})
        try:
            self.plot.setViewport(QtWidgets.QOpenGLWidget())
        except Exception:
            pass
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.price_curve = self.plot.plot(pen=pg.mkPen(brand.ACCENT, width=2))
        self.fill_scatter = pg.ScatterPlotItem(symbol="o", size=8, brush=pg.mkBrush(brand.SUCCESS))
        self.plot.addItem(self.fill_scatter)
        self.candle_item = CandlestickItem()
        self.plot.addItem(self.candle_item)
        self.ts: list[float] = []
        self.prices: list[float] = []
        self.fills: list[dict] = []
        self.candles: list[dict] = []
        self.candle_times: list[float] = []
        self.mode = "line"  # or "candles"

        # toggle buttons
        btn_line = QtWidgets.QPushButton("Line")
        btn_candles = QtWidgets.QPushButton("Candles")
        btn_line.setCheckable(True)
        btn_candles.setCheckable(True)
        btn_line.setChecked(True)
        btn_line.clicked.connect(lambda: self._set_mode("line", btn_line, btn_candles))
        btn_candles.clicked.connect(lambda: self._set_mode("candles", btn_line, btn_candles))
        btn_bar = QtWidgets.QHBoxLayout()
        btn_bar.addWidget(btn_line)
        btn_bar.addWidget(btn_candles)
        btn_bar.addStretch()
        self.crosshair_info = QtWidgets.QLabel("")
        self.crosshair_info.setStyleSheet("color: #e0e6ed;")
        btn_bar.addWidget(self.crosshair_info)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(btn_bar)
        layout.addWidget(self.plot)
        self.setLayout(layout)

        bridge.microstructureUpdated.connect(self.on_snapshot)
        bridge.orderStatusUpdated.connect(self.on_order)
        bridge.chartUpdated.connect(self.on_candle)
        # crosshair
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#556"))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#556"))
        self.plot.addItem(self.vLine, ignoreBounds=True)
        self.plot.addItem(self.hLine, ignoreBounds=True)
        self.proxy = pg.SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=60, slot=self._mouse_moved)
        self.plot.plotItem.showGrid(x=True, y=True, alpha=0.3)
        self.plot.plotItem.setMouseEnabled(x=True, y=True)
        self.plot.plotItem.setMenuEnabled(False)
        self.plot.plotItem.getAxis("left").setPen(pg.mkPen("#556"))
        self.plot.plotItem.getAxis("bottom").setPen(pg.mkPen("#556"))

    def on_snapshot(self, snap: dict) -> None:
        mid = snap.get("mid") or snap.get("price")
        if mid is None:
            return
        try:
            mid_f = float(mid)
        except Exception:
            return
        now_ts = time.time()
        self.ts.append(now_ts)
        self.prices.append(mid_f)
        if self.mode == "line":
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

    def on_candle(self, bar: dict) -> None:
        self.candles.append(bar)
        self.candle_times.append(bar.get("time", len(self.candles)))
        if self.mode == "candles":
            self._draw_candles()

    def _set_mode(self, mode: str, btn_line: QtWidgets.QPushButton, btn_candles: QtWidgets.QPushButton) -> None:
        self.mode = mode
        btn_line.setChecked(mode == "line")
        btn_candles.setChecked(mode == "candles")
        if mode == "line":
            self.price_curve.setVisible(True)
            self._draw_line()
        else:
            self.price_curve.setVisible(False)
            self._draw_candles()

    def _draw_line(self) -> None:
        self.price_curve.setData(self.ts, self.prices)

    def _draw_candles(self) -> None:
        if not self.candles:
            return
        data = []
        candles = self.candles[-300:]
        times = self.candle_times[-300:] if len(self.candle_times) >= len(candles) else list(range(len(candles)))
        for i, c in enumerate(candles):
            x = times[i] if i < len(times) else i
            data.append((x, c["open"], c["high"], c["low"], c["close"]))
        self.candle_item.setData(data)
        self.time_axis.set_times(times)

    def _mouse_moved(self, evt) -> None:
        pos = evt[0]
        if self.plot.sceneBoundingRect().contains(pos):
            mousePoint = self.plot.plotItem.vb.mapSceneToView(pos)
            x = mousePoint.x()
            y = mousePoint.y()
            self.vLine.setPos(x)
            self.hLine.setPos(y)
            # show price/time crosshair info
            if self.candle_times:
                idx = min(range(len(self.candle_times)), key=lambda i: abs(self.candle_times[i] - x))
                idx = max(0, min(idx, len(self.candles) - 1))
                c = self.candles[idx]
                t_fmt = time.strftime("%H:%M:%S", time.localtime(self.candle_times[idx]))
                self.crosshair_info.setText(
                    f"{t_fmt} O={c['open']:.2f} H={c['high']:.2f} L={c['low']:.2f} C={c['close']:.2f} | y={y:.2f}"
                )


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
        on_switch_symbol: Optional[Callable[[str], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self.on_submit_order = on_submit_order
        self.on_cancel_order = on_cancel_order
        self.provider_manager = provider_manager
        self.bus = event_bus
        self.pm_settings = pm_settings or {}
        self._on_switch_symbol = on_switch_symbol
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
        self.provider_debug = ProviderDebugPanel()
        self.execution_mode_label = QtWidgets.QLabel(f"Exec: {getattr(provider_manager, 'execution_mode', 'SIM')}")

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
        self.provider_debug.connect_bridge(bridge)
        self.market_watch.connect_bridge(bridge)
        self.status_widget.connect_bridge(bridge, mode=mode)

        # DockArea layout
        self.area.addDock(Dock("Chart", widget=self.chart))
        # Left column: MarketWatch + Footprint, DOM stacked nearby
        self.area.addDock(Dock("MarketWatch", widget=self.market_watch), "left", self.area.docks["Chart"])
        self.area.addDock(Dock("Footprint", widget=self.footprint_panel), "bottom", self.area.docks["MarketWatch"])
        self.area.addDock(Dock("DOM", widget=self.dom_panel), "right", self.area.docks["MarketWatch"])
        self.area.addDock(Dock("Delta", widget=self.delta_panel), "above", self.area.docks["DOM"])
        # Center: Chart + Tape + Metrics
        self.area.addDock(Dock("Tape", widget=self.tape_panel), "bottom", self.area.docks["Chart"])
        self.area.addDock(Dock("Metrics", widget=self.metrics_panel), "bottom", self.area.docks["Tape"])
        # Right: Strategy/Execution/Vol/Regime/Liquidity/VolumeProfile stack
        self.area.addDock(Dock("Strategy", widget=self.strategy_panel), "right", self.area.docks["Chart"])
        self.area.addDock(Dock("Execution", widget=self.execution_panel), "bottom", self.area.docks["Strategy"])
        self.area.addDock(Dock("Liquidity", widget=self.liquidity_panel), "bottom", self.area.docks["Execution"])
        self.area.addDock(Dock("VolumeProfile", widget=self.vol_profile_panel), "bottom", self.area.docks["Liquidity"])
        self.area.addDock(Dock("Regime", widget=self.regime_panel), "bottom", self.area.docks["VolumeProfile"])
        self.area.addDock(Dock("Volatility", widget=self.vol_panel), "bottom", self.area.docks["Regime"])
        # Logs and Debug
        self.area.addDock(Dock("Logs", widget=self.logs_panel), "bottom", self.area.docks["Metrics"])
        self.area.addDock(Dock("ProviderDebug", widget=self.provider_debug), "bottom", self.area.docks["Logs"])

        self.statusBar().addPermanentWidget(self.status_widget)
        self.statusBar().addPermanentWidget(self.execution_mode_label)

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

        presets_menu = menubar.addMenu("Layout Presets")
        presets_menu.addAction("Preset 1 - Scalping XAUUSD").triggered.connect(lambda: self._apply_preset("scalping"))
        presets_menu.addAction("Preset 2 - Institutional BTC").triggered.connect(lambda: self._apply_preset("btc"))
        presets_menu.addAction("Preset 3 - Futures CME").triggered.connect(lambda: self._apply_preset("cme"))
        presets_menu.addAction("Preset 4 - Custom (save current)").triggered.connect(lambda: self.workspace.save_profile("custom"))

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
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F1"), self, activated=lambda: self._apply_preset("scalping"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F2"), self, activated=lambda: self._apply_preset("btc"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F3"), self, activated=lambda: self._apply_preset("cme"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F4"), self, activated=lambda: self._apply_preset("custom"))
        # status FPS monitor placeholder
        from ui.perf_monitor import FPSMonitor

        self.fps_monitor = FPSMonitor(self.statusBar())
        self.statusBar().addPermanentWidget(self.fps_monitor)
        import ui.helpers as helpers

        helpers.FPS_MONITOR = self.fps_monitor

    def _on_mode_change(self, mode: str) -> None:
        self.status_widget.mode_label.setText(f"Mode: {mode}")

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "Bots Institucionais UI\nPhases I–VII\nEvent-driven microstructure + execution stack.\n"
            "Shortcuts:\n"
            "Ctrl+F1/F2/F3/F4: Layout presets\n"
            "Double-click MarketWatch row: Apply instrument\n"
            "Ctrl+1/Ctrl+2: Cycle watchlist",
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
        if cfg.get("provider") and self._on_switch_symbol:
            self._on_switch_symbol(cfg.get("symbol") or self.pm_settings.get("market_symbol", ""))
            self.status_widget.conn_label.setText(f"Conn: {cfg['provider']}")

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
        if self._on_switch_symbol:
            self._on_switch_symbol(symbol)
            self.statusBar().showMessage(f"[MarketWatch] User selected {symbol}", 3000)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.save_state()
        super().closeEvent(event)

    def _apply_preset(self, name: str) -> None:
        """Simple dock arrangement presets."""
        area = self.area
        try:
            if name == "scalping":
                area.moveDock(area.docks["DOM"], "left", area.docks["Chart"])
                area.moveDock(area.docks["Footprint"], "right", area.docks["DOM"])
                area.moveDock(area.docks["Tape"], "right", area.docks["Footprint"])
            elif name == "btc":
                area.moveDock(area.docks["Chart"], "above", area.docks["DOM"])
                area.moveDock(area.docks["Liquidity"], "right", area.docks["Chart"])
                area.moveDock(area.docks["Footprint"], "bottom", area.docks["Chart"])
            elif name == "cme":
                area.moveDock(area.docks["Heatmap"], "above", area.docks.get("Footprint", area.docks["Chart"]))
                area.moveDock(area.docks["VolumeProfile"], "right", area.docks["Heatmap"])
                area.moveDock(area.docks["Strategy"], "right", area.docks["VolumeProfile"])
            else:
                self.workspace.save_profile("custom")
        except Exception:
            pass

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
