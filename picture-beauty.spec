# -*- mode: python ; coding: utf-8 -*-
# PyInstaller：单文件、无控制台。项目根目录执行：
#   pyinstaller --clean --noconfirm picture-beauty.spec

a = Analysis(
    ["enhance_gui.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["enhance_for_social"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="PictureBeauty",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
