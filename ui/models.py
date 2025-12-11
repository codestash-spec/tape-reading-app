from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PySide6 import QtCore, QtGui


class BaseTableModel(QtCore.QAbstractTableModel):
    def __init__(self, headers: List[str]) -> None:
        super().__init__()
        self.headers = headers
        self.rows: List[List[Any]] = []

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self.rows)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self.headers)

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.headers[section]
        return str(section)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        value = self.rows[index.row()][index.column()]
        if role == QtCore.Qt.DisplayRole:
            return value
        return None

    def reset_with_rows(self, rows: List[List[Any]]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class DomTableModel(BaseTableModel):
    """
    DOM ladder with memory of previous levels to highlight stacking/pulling in delegates.
    """

    def __init__(self) -> None:
        super().__init__(["Price", "Bid Size", "Ask Size", "Liquidity"])
        self.prev: Dict[float, Tuple[float, float]] = {}

    def update_from_dom(self, ladder: List[Tuple[float, float, float, float]]) -> None:
        rows = []
        new_prev: Dict[float, Tuple[float, float]] = {}
        for p, b, a, l in ladder:
            rows.append([p, b, a, l])
            new_prev[p] = (b, a)
        self.prev = new_prev
        self.reset_with_rows(rows)


class TapeTableModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Time", "Price", "Size", "Side", "Flags"])

    def flags_for_trade(self, trade: Dict[str, Any]) -> str:
        flags = []
        if trade.get("size", 0) and float(trade["size"]) > 100:
            flags.append("BLOCK")
        if trade.get("speed", 0) and float(trade["speed"]) > 5:
            flags.append("FAST")
        return ",".join(flags)

    def append_trade(self, trade: Dict[str, Any]) -> None:
        ts = trade.get("ts") or datetime.utcnow().strftime("%H:%M:%S")
        row = [
            ts,
            float(trade.get("price", 0)),
            float(trade.get("size", 0)),
            trade.get("side", "?"),
            trade.get("flags", self.flags_for_trade(trade)),
        ]
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.rows.insert(0, row)
        self.endInsertRows()


class FootprintModel(QtCore.QObject):
    """
    Footprint matrix representation for custom painting.
    """

    changed = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.matrix: Dict[float, Dict[str, float]] = {}

    def update_footprint(self, footprint: Dict[float, Dict[str, float]]) -> None:
        self.matrix = footprint
        self.changed.emit()


class DeltaSeriesModel(QtCore.QObject):
    """
    Holds a time series for pyqtgraph plotting.
    """

    changed = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.ts: List[float] = []
        self.values: List[float] = []

    def append_delta(self, ts: datetime, value: float) -> None:
        self.ts.append(ts.timestamp())
        self.values.append(value)
        self.changed.emit()


class StrategySignalsModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Time", "Symbol", "Direction", "Score", "Tags"])

    def append_signal(self, sig: Dict[str, Any]) -> None:
        ts_val: Any = sig.get("timestamp", datetime.utcnow())
        if hasattr(ts_val, "strftime"):
            ts_str = ts_val.strftime("%H:%M:%S")
        else:
            ts_str = str(ts_val)
        row = [
            ts_str,
            sig.get("symbol", ""),
            sig.get("direction", ""),
            float(sig.get("score", 0.0)),
            sig.get("metadata", {}).get("tags", ""),
        ]
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.rows.insert(0, row)
        self.endInsertRows()


class ExecutionOrdersModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Order ID", "Symbol", "Side", "Status", "Qty", "AvgPx", "Slippage"])

    def upsert_order(self, evt: Dict[str, Any]) -> None:
        oid = evt.get("order_id", "")
        existing_idx = next((i for i, r in enumerate(self.rows) if r[0] == oid), None)
        row = [
            oid,
            evt.get("symbol", ""),
            evt.get("side", ""),
            evt.get("status", ""),
            float(evt.get("filled_qty", evt.get("quantity", 0))),
            float(evt.get("avg_price", evt.get("limit_price", 0) or 0)),
            float(evt.get("slippage_bps", 0)),
        ]
        if existing_idx is None:
            self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
            self.rows.insert(0, row)
            self.endInsertRows()
        else:
            self.rows[existing_idx] = row
            top_left = self.index(existing_idx, 0)
            bottom_right = self.index(existing_idx, len(self.headers) - 1)
            self.dataChanged.emit(top_left, bottom_right, [])  # type: ignore[arg-type]


class MetricsModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Metric", "Value"])

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        rows = [[k, str(v)] for k, v in metrics.items()]
        self.reset_with_rows(rows)


class LogModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Record"])

    def append(self, record: str) -> None:
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.rows.insert(0, [record])
        self.endInsertRows()


@dataclass
class ExecutionMarker:
    ts: float
    price: float
    side: str
    qty: float
