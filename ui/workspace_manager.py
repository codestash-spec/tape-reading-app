from __future__ import annotations

import base64
import json
from typing import Dict

from PySide6 import QtCore, QtWidgets


class WorkspaceManager:
    """
    Saves/restores dock layout profiles to JSON + QSettings.
    """

    def __init__(self, window: QtWidgets.QMainWindow, settings: QtCore.QSettings) -> None:
        self.window = window
        self.settings = settings

    def save_profile(self, name: str) -> Dict[str, str]:
        geometry = self.window.saveGeometry()
        state = self.window.saveState()
        profile = {
            "geometry": base64.b64encode(bytes(geometry)).decode("utf-8"),
            "state": base64.b64encode(bytes(state)).decode("utf-8"),
        }
        self.settings.setValue(f"workspace/{name}", json.dumps(profile))
        self.settings.sync()
        return profile

    def load_profile(self, name: str) -> bool:
        raw = self.settings.value(f"workspace/{name}")
        if not raw:
            return False
        profile = json.loads(raw)
        geom = QtCore.QByteArray.fromBase64(profile["geometry"].encode("utf-8"))
        state = QtCore.QByteArray.fromBase64(profile["state"].encode("utf-8"))
        self.window.restoreGeometry(geom)
        self.window.restoreState(state)
        return True

    def ensure_default(self) -> None:
        if not self.settings.value("workspace/default"):
            self.save_profile("default")

