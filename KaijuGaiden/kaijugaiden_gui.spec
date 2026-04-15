# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path.cwd()
BUILD_DIR = ROOT / 'build'
OPTIONAL_BINARIES = []
wrapper = BUILD_DIR / 'xinput_wrapper.dll'
if wrapper.exists():
    OPTIONAL_BINARIES.append((str(wrapper), 'build'))


a = Analysis(
    ['host_graphical.py'],
    pathex=[],
    binaries=OPTIONAL_BINARIES,
    datas=[('assets', 'assets'), ('assets/placeholderassets', 'assets/placeholderassets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='kaijugaiden_windows_xbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
