from __future__ import annotations

from typing import Dict, List, Tuple

from PySide6 import QtWidgets

from ui.models import DomTableModel
from ui.event_bridge import EventBridge


class DomPanel(QtWidgets.QWidget):
    """
    Displays DOM ladder with liquidity hints.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = DomTableModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.domUpdated.connect(self.update_dom)

    def update_dom(self, payload: Dict) -> None:
        ladder = payload.get("ladder") or payload.get("levels") or {}
        rows: List[Tuple[float, float, float, float]] = []
        if isinstance(ladder, dict):
            for price_str, sizes in ladder.items():
                price = float(price_str)
                bid = float(sizes.get("bid", 0.0) if isinstance(sizes, dict) else sizes or 0.0)
                ask = float(sizes.get("ask", 0.0) if isinstance(sizes, dict) else 0.0)
                liq = float(sizes.get("liquidity", 0.0)) if isinstance(sizes, dict) else 0.0
                rows.append((price, bid, ask, liq))
        elif isinstance(ladder, list):
            for level in ladder:
                price = float(level.get("price", 0.0))
                bid = float(level.get("bid", 0.0))
                ask = float(level.get("ask", 0.0))
                liq = float(level.get("liquidity", 0.0))
                rows.append((price, bid, ask, liq))
        rows = sorted(rows, key=lambda r: r[0], reverse=True)
        self.model.update_from_dom(rows)

