from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from PySide6 import QtCore


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
    def __init__(self) -> None:
        super().__init__(["Price", "Bid Size", "Ask Size", "Liquidity"])

    def update_from_dom(self, ladder: List[Tuple[float, float, float, float]]) -> None:
        rows = [[f"{p:.2f}", f"{b:.0f}", f"{a:.0f}", f"{l:.2f}"] for p, b, a, l in ladder]
        self.reset_with_rows(rows)


class TapeTableModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Time", "Price", "Size", "Side", "Flags"])

    def append_trade(self, trade: Dict[str, Any]) -> None:
        ts = trade.get("ts") or datetime.utcnow().strftime("%H:%M:%S")
        row = [
            ts,
            f\"{trade.get('price', 0):.2f}\",
            f\"{trade.get('size', 0):.0f}\",
            trade.get(\"side\", \"?\"),
            trade.get(\"flags\", \"\"),
        ]
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.rows.insert(0, row)
        self.endInsertRows()


class FootprintModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Price", "Buy Vol", "Sell Vol", "Imbalance"])

    def update_footprint(self, footprint: Dict[float, Dict[str, float]]) -> None:
        rows: List[List[Any]] = []
        for price, vols in sorted(footprint.items(), reverse=True):
            buy = vols.get("buy", 0.0)
            sell = vols.get("sell", 0.0)
            imbalance = buy - sell
            rows.append([f"{price:.2f}", f"{buy:.0f}", f"{sell:.0f}", f"{imbalance:.0f}"])
        self.reset_with_rows(rows)


class DeltaSeriesModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Time", "CVD"])

    def append_delta(self, ts: datetime, value: float) -> None:
        row = [ts.strftime("%H:%M:%S"), f"{value:.0f}"]
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.rows.insert(0, row)
        self.endInsertRows()


class StrategySignalsModel(BaseTableModel):
    def __init__(self) -> None:
        super().__init__(["Time", "Symbol", "Direction", "Score", "Tags"])

    def append_signal(self, sig: Dict[str, Any]) -> None:
        row = [
            sig.get("timestamp", datetime.utcnow()).strftime("%H:%M:%S") if hasattr(sig.get("timestamp"), "strftime") else str(sig.get("timestamp", "")),
            sig.get("symbol", ""),
            sig.get("direction", ""),
            f"{sig.get('score', 0):.2f}",
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
            f"{evt.get('filled_qty', 0):.2f}",
            f\"{evt.get('avg_price', evt.get('limit_price', 0) or 0):.2f}\",
            f\"{evt.get('slippage_bps', 0):.2f}\",
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

