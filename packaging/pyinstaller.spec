# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for Marketing Intelligence Studio.

PyInstaller does not cross-compile — this MUST be run on the target OS:

    Windows:  build on a Windows machine ->  dist/Marketing Intelligence Studio/Marketing Intelligence Studio.exe
    macOS:    build on a macOS machine   ->  dist/Marketing Intelligence Studio.app

See packaging/build_windows.bat and packaging/build_macos.sh, or the
".github/workflows/build-release.yml" CI workflow, which runs this on real
Windows/macOS GitHub Actions runners.

This bundles the Python interpreter, tkinter, and all pip dependencies into
the app — end users need nothing installed. It does NOT bundle `clients/`,
`.env.example`, or install instructions; those ship alongside the built app
as plain files (see the Release/ folder), not inside the frozen bundle, so
a non-technical user (or an admin) can edit client data or credentials
without needing to touch the packaged app at all.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

APP_NAME = "Marketing Intelligence Studio"
# PyInstaller executes .spec files via exec() without a real `__file__`; it
# injects `SPECPATH` (this spec's own directory) instead.
REPO_ROOT = Path(SPECPATH).resolve().parent

hidden_imports = (
    collect_submodules("praw")
    + collect_submodules("prawcore")
    + ["pydantic_settings", "dotenv"]
)

a = Analysis(
    [str(REPO_ROOT / "frontend" / "app.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    strip=False,
    upx=False,
    console=False,  # windowed app — no terminal window pops up
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.marketingintelligencestudio.desktop",
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
