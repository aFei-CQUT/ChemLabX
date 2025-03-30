# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['E:\\1.LGRepository\\ChemLabX1.0'],
    binaries=[('D:/Anaconda/envs/new_env/python39.dll', '.')],  # 添加 python39.dll
    datas=[('logos/ce.ico', 'logos')],  # 包含图标文件
    hiddenimports=['gui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 如果不需要控制台窗口
    icon='logos/ce.ico',  # 指定图标
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
