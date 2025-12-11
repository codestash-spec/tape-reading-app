from __future__ import annotations

from typing import Callable, Optional

from PySide6 import QtCore, QtWidgets

from models.order import OrderRequest, OrderSide, OrderType


class OrderTicket(QtWidgets.QWidget):
    """
    Bloomberg EMSX-style order ticket wired to execution callbacks.
    """

    submitted = QtCore.Signal(OrderRequest)
    canceled = QtCore.Signal(str)

    def __init__(self, on_submit: Optional[Callable[[OrderRequest], None]] = None, on_cancel: Optional[Callable[[str], None]] = None, parent=None) -> None:
        super().__init__(parent)
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.setWindowTitle("Order Ticket")

        self.symbol = QtWidgets.QLineEdit("XAUUSD")
        self.side = QtWidgets.QComboBox()
        self.side.addItems([OrderSide.BUY.value, OrderSide.SELL.value])
        self.otype = QtWidgets.QComboBox()
        self.otype.addItems([ot.value for ot in OrderType])
        self.qty = QtWidgets.QDoubleSpinBox()
        self.qty.setMaximum(1e9)
        self.qty.setDecimals(2)
        self.qty.setValue(1.0)
        self.limit = QtWidgets.QDoubleSpinBox()
        self.limit.setMaximum(1e9)
        self.limit.setDecimals(4)
        self.stop = QtWidgets.QDoubleSpinBox()
        self.stop.setMaximum(1e9)
        self.stop.setDecimals(4)
        self.tif = QtWidgets.QComboBox()
        self.tif.addItems(["DAY", "GTC", "IOC", "FOK"])
        self.reduce_only = QtWidgets.QCheckBox("Reduce only")
        self.client_tag = QtWidgets.QLineEdit()

        form = QtWidgets.QFormLayout()
        form.addRow("Symbol", self.symbol)
        form.addRow("Side", self.side)
        form.addRow("Type", self.otype)
        form.addRow("Quantity", self.qty)
        form.addRow("Limit", self.limit)
        form.addRow("Stop", self.stop)
        form.addRow("TIF", self.tif)
        form.addRow(self.reduce_only)
        form.addRow("Client Tag", self.client_tag)

        self.submit_btn = QtWidgets.QPushButton("Submit")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.submit_btn.clicked.connect(self._submit)
        self.cancel_btn.clicked.connect(self._cancel)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.submit_btn)
        btns.addWidget(self.cancel_btn)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btns)
        self.setLayout(layout)

    def _submit(self) -> None:
        order = OrderRequest(
            order_id="ui-" + QtCore.QDateTime.currentDateTimeUtc().toString("yyyyMMddhhmmsszzz"),
            symbol=self.symbol.text().strip().upper(),
            side=OrderSide(self.side.currentText()),
            quantity=float(self.qty.value()),
            order_type=OrderType(self.otype.currentText()),
            limit_price=float(self.limit.value()) if self.limit.value() else None,
            stop_price=float(self.stop.value()) if self.stop.value() else None,
            tif=self.tif.currentText(),
            reduce_only=self.reduce_only.isChecked(),
            metadata={"client_tag": self.client_tag.text()},
        )
        self.submitted.emit(order)
        if self.on_submit:
            self.on_submit(order)

    def _cancel(self) -> None:
        oid = self.symbol.text().strip().upper()
        self.canceled.emit(oid)
        if self.on_cancel:
            self.on_cancel(oid)
