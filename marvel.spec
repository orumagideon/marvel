# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Marvel Trading Dashboard
Run: pyinstaller marvel.spec
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

icon_path = 'app_icon.ico' if Path('app_icon.ico').exists() else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('data', 'data'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'MetaTrader5',
        'customtkinter',
        'cryptography',
        'cryptography.fernet',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MarvelTradingDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want console window visible
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
