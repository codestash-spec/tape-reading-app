from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets


class SettingsWindow(QtWidgets.QDialog):
    """
    Configurable settings window with tabs.
    """

    def __init__(self, settings: Dict[str, object], on_apply=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self.on_apply = on_apply
        self.tabs = QtWidgets.QTabWidget()

        self.theme_tab = self._build_theme_tab()
        self.backend_tab = self._build_backend_tab()
        self.risk_tab = self._build_risk_tab()
        self.exec_tab = self._build_exec_tab()
        self.log_tab = self._build_log_tab()
        self.performance_tab = self._build_perf_tab()

        self.tabs.addTab(self.theme_tab, "Theme")
        self.tabs.addTab(self.backend_tab, "Backend")
        self.tabs.addTab(self.risk_tab, "Risk")
        self.tabs.addTab(self.exec_tab, "Execution")
        self.tabs.addTab(self.log_tab, "Logging")
        self.tabs.addTab(self.performance_tab, "Performance")

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.apply)
        btns.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(btns)
        self.setLayout(layout)

    def _build_theme_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Theme", self.theme_combo)
        return w

    def _build_backend_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["live", "paper", "replay", "sim"])
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItems(["SIM", "IBKR", "CME", "BINANCE", "OKX"])
        self.dom_depth_combo = QtWidgets.QComboBox()
        self.dom_depth_combo.addItems(["10", "20", "50", "100"])
        self.delta_mode_combo = QtWidgets.QComboBox()
        self.delta_mode_combo.addItems(["stream", "cumulative", "footprint"])
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Mode", self.mode_combo)
        layout.addRow("Provider", self.provider_combo)
        layout.addRow("DOM Depth", self.dom_depth_combo)
        layout.addRow("Delta Mode", self.delta_mode_combo)
        return w

    def _build_risk_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        self.max_size = QtWidgets.QDoubleSpinBox()
        self.max_size.setMaximum(1e9)
        self.max_exposure = QtWidgets.QDoubleSpinBox()
        self.max_exposure.setMaximum(1e9)
        self.throttle = QtWidgets.QSpinBox()
        self.throttle.setMaximum(100000)
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Max size", self.max_size)
        layout.addRow("Max exposure", self.max_exposure)
        layout.addRow("Throttle max", self.throttle)
        return w

    def _build_exec_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        self.slippage = QtWidgets.QDoubleSpinBox()
        self.slippage.setSuffix(" bps")
        self.slippage.setMaximum(10000)
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Slippage tolerance", self.slippage)
        return w

    def _build_log_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        self.log_level = QtWidgets.QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Log level", self.log_level)
        return w

    def _build_perf_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        self.buffer = QtWidgets.QSpinBox()
        self.buffer.setMaximum(1000000)
        self.update_freq = QtWidgets.QDoubleSpinBox()
        self.update_freq.setMaximum(10.0)
        self.update_freq.setValue(0.25)
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Buffer size", self.buffer)
        layout.addRow("Update freq (s)", self.update_freq)
        return w

    def apply(self) -> None:
        if self.on_apply:
            self.on_apply(
                {
                    "theme": self.theme_combo.currentText(),
                    "mode": self.mode_combo.currentText(),
                    "provider": self.provider_combo.currentText(),
                    "dom_depth": int(self.dom_depth_combo.currentText()),
                    "delta_mode": self.delta_mode_combo.currentText(),
                    "risk": {
                        "max_size": self.max_size.value(),
                        "max_exposure": self.max_exposure.value(),
                        "throttle_max": self.throttle.value(),
                    },
                    "execution": {"slippage_bps": self.slippage.value()},
                    "log_level": self.log_level.currentText(),
                    "performance": {"buffer": self.buffer.value(), "update_freq": self.update_freq.value()},
                }
            )
        self.accept()
