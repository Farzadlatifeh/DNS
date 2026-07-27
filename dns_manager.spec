# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DNS Manager GUI
Build command: pyinstaller --clean dns_manager.spec

IMPORTANT: This must be run on Windows to create a .exe file.
The application is designed for Windows 11 and uses Windows-specific APIs.
"""

block_cipher = None

a = Analysis(
    ['dns_manager_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('dns_profiles.json', '.'),
        ('extract_dns.py', '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'qt_material',
        'json',
        'subprocess',
        'socket',
        'ctypes',
        're',
        'pathlib',
        'urllib.request',
        'importlib.util',
        'io',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide2',
        'PySide2.QtCore',
        'PySide2.QtGui',
        'PySide2.QtWidgets',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DNS_Shecan',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='faveicon.ico',          # relative path, ensure file exists
)