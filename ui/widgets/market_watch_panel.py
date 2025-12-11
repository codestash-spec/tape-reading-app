from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from PySide6 import QtCore, QtWidgets

from ui.event_bridge import EventBridge


DEFAULT_WATCHLISTS = {
    "default": ["BTCUSDT", "XAUUSD", "GC", "ETHUSDT"],
    "crypto": ["BTCUSDT", "ETHUSDT"],
    "futures": ["GC", "ES", "NQ"],
}


class MarketWatchPanel(QtWidgets.QWidget):
    instrumentSelected = QtCore.Signal(str)

    def __init__(self, watchlist_path: str = "settings/watchlists.json", parent=None) -> None:
        super().__init__(parent)
        self.watchlist_path = watchlist_path
        self.watchlists = self._load_watchlists()
        self.favorites: set[str] = set()

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Symbol", "Last", "Chg%", "Provider", "Apply", "★"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self._on_cell_clicked)

        self.add_btn = QtWidgets.QPushButton("+ Add Instrument")
        self.add_btn.clicked.connect(self._add_instrument)

        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItems(list(self.watchlists.keys()))
        self.preset_combo.currentTextChanged.connect(self._load_preset)

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(QtWidgets.QLabel("Watchlist:"))
        top_layout.addWidget(self.preset_combo)
        top_layout.addStretch()
        top_layout.addWidget(self.add_btn)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self._populate(self.watchlists.get("default", []))
        self._initial_applied = False

    def _load_watchlists(self) -> Dict[str, List[str]]:
        if not os.path.exists(self.watchlist_path):
            os.makedirs(os.path.dirname(self.watchlist_path) or ".", exist_ok=True)
            with open(self.watchlist_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_WATCHLISTS, f, indent=2)
            return DEFAULT_WATCHLISTS
        try:
            with open(self.watchlist_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_WATCHLISTS

    def _save_watchlists(self) -> None:
        os.makedirs(os.path.dirname(self.watchlist_path) or ".", exist_ok=True)
        with open(self.watchlist_path, "w", encoding="utf-8") as f:
            json.dump(self.watchlists, f, indent=2)

    def _populate(self, symbols: List[str]) -> None:
        self.table.setRowCount(0)
        for sym in symbols:
            self._add_row(sym)

    def _add_row(self, symbol: str, provider: str = "?") -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(symbol))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem("-"))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem("-"))
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(provider))

        apply_btn = QtWidgets.QPushButton("Apply")
        apply_btn.clicked.connect(lambda _, s=symbol: self.instrumentSelected.emit(s))
        self.table.setCellWidget(row, 4, apply_btn)

        fav_btn = QtWidgets.QPushButton("☆")
        fav_btn.clicked.connect(lambda _, s=symbol: self._toggle_fav(s, fav_btn))
        self.table.setCellWidget(row, 5, fav_btn)

    def _toggle_fav(self, symbol: str, btn: QtWidgets.QPushButton) -> None:
        if symbol in self.favorites:
            self.favorites.remove(symbol)
            btn.setText("☆")
        else:
            self.favorites.add(symbol)
            btn.setText("★")

    def _add_instrument(self) -> None:
        text, ok = QtWidgets.QInputDialog.getText(self, "Add Instrument", "Symbol:")
        if ok and text:
            sym = text.strip().upper()
            current_list = self.preset_combo.currentText()
            lst = self.watchlists.setdefault(current_list, [])
            if sym not in lst:
                lst.append(sym)
                self._save_watchlists()
                self._populate(lst)

    def _load_preset(self, name: str) -> None:
        self._populate(self.watchlists.get(name, []))

    def connect_bridge(self, bridge: EventBridge) -> None:
        self._bridge = bridge
        # listen for quotes/trades to update last/var%
        bridge.bus.subscribe("trade", self._on_trade)
        bridge.bus.subscribe("quote", self._on_quote)

    def disconnect_bridge(self) -> None:
        if getattr(self, "_bridge", None):
            self._bridge.bus.unsubscribe("trade", self._on_trade)
            self._bridge.bus.unsubscribe("quote", self._on_quote)
            self._bridge = None

    def _update_price(self, symbol: str, price: float, provider: Optional[str] = None) -> None:
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == symbol:
                last_item = self.table.item(row, 1)
                prev = last_item.text()
                try:
                    prev_val = float(prev)
                except Exception:
                    prev_val = price
                last_item.setText(f"{price:.2f}")
                chg = ((price - prev_val) / prev_val * 100) if prev_val else 0.0
                chg_item = self.table.item(row, 2)
                chg_item.setText(f"{chg:.2f}%")
                if chg > 0:
                    chg_item.setForeground(QtCore.Qt.green)
                elif chg < 0:
                    chg_item.setForeground(QtCore.Qt.red)
                if provider:
                    prov_item = self.table.item(row, 3)
                    if prov_item:
                        prov_item.setText(provider)
                break

    def _on_trade(self, evt) -> None:
        sym = evt.symbol
        price = evt.payload.get("price")
        if price is None:
            return
        source = getattr(evt, "source", None) or evt.payload.get("provider")
        self._update_price(sym, float(price), provider=source)

    def _on_quote(self, evt) -> None:
        sym = evt.symbol
        price = evt.payload.get("last") or evt.payload.get("mid")
        if price is None:
            return
        source = getattr(evt, "source", None) or evt.payload.get("provider")
        self._update_price(sym, float(price), provider=source)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        if col == 0:
            sym = self.table.item(row, 0).text()
            self.instrumentSelected.emit(sym)

    def apply_on_start(self, symbol: str) -> None:
        """Selects and emits the given symbol once on startup."""
        if self._initial_applied:
            return
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text().upper() == symbol.upper():
                self.table.selectRow(row)
                self.instrumentSelected.emit(symbol)
                self._initial_applied = True
                break
