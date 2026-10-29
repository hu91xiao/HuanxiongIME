# -*- mode: python ; coding: utf-8 -*-
# 幻熊输入法设置面板 —— PyInstaller 打包描述
# 用 onedir（免解包），主程序只有几 MB，启动快、不依赖 %TEMP%

import os

ROOT = os.path.abspath(os.getcwd())

a = Analysis(
    [os.path.join(ROOT, 'src', 'settings', 'app.py')],
    pathex=[os.path.join(ROOT, 'src', 'settings')],
    binaries=[],
    datas=[(os.path.join(ROOT, 'src', 'settings', 'ui.html'), '.')],
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
    [],
    exclude_binaries=True,
    name='HuanxiongSettings',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'assets', 'huanxiong.ico')],
    contents_directory='HuanxiongSettings_data',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='HuanxiongSettings',
)
