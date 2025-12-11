from __future__ import annotations

from PySide6 import QtGui

from ui.themes import brand


class Theme:
    """
    Holds palette and typography definitions for the institutional UI.
    """

    def __init__(self, mode: str = "dark") -> None:
        self.mode = mode
        self.palette = self._build_palette(mode)
        self.font = QtGui.QFont(brand.FONT_FAMILY, brand.FONT_SIZE)

    def _build_palette(self, mode: str) -> QtGui.QPalette:
        palette = QtGui.QPalette()
        if mode == "dark":
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(brand.BG_DARK))
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(brand.TEXT_LIGHT))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0f1f3d"))
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#1b2b4d"))
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor(brand.TEXT_LIGHT))
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#1c2541"))
            palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(brand.TEXT_LIGHT))
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#3a506b"))
            palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))
        else:
            palette = QtGui.QPalette()
        return palette

