"""
PyInstaller Configuration for Marvel Trading Dashboard
Builds standalone Windows executable for VPS deployment
"""

import PyInstaller.config
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Hidden imports
hiddenimports = [
    'MetaTrader5',
    'customtkinter',
    'cryptography.fernet',
    'pandas',
]

# Data files to include
datas = [
    ('app', 'app'),
    ('logs', 'logs'),
    ('data', 'data'),
]

# Exclusions to reduce size
excludedimports = [
    'tkinter',
    'matplotlib',
    'numpy',
]

# Binary dependencies
binaries = []
