# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = collect_submodules("PySide6") + ["pyqtgraph"]

a = Analysis(
    ["ui/app.py"],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        ("ui/themes/institutional_dark.qss", "ui/themes"),
        ("ui/themes/institutional_light.qss", "ui/themes"),
        ("ui/themes/icons/*.svg", "ui/themes/icons"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="tape-reading-app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="tape-reading-app",
)
