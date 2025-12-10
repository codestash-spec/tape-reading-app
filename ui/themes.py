from __future__ import annotations

from PySide6 import QtGui


class Theme:
    """
    Holds palette and typography definitions for the institutional UI.
    """

    def __init__(self, mode: str = "dark") -> None:
        self.mode = mode
        self.palette = self._build_palette(mode)
        self.font = QtGui.QFont("Segoe UI", 9)

    def _build_palette(self, mode: str) -> QtGui.QPalette:
        palette = QtGui.QPalette()
        if mode == "dark":
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0b132b"))
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#e0e6ed"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0f1f3d"))
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#1b2b4d"))
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#e0e6ed"))
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#1c2541"))
            palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#e0e6ed"))
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#3a506b"))
            palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))
        else:
            palette = QtGui.QPalette()
        return palette

