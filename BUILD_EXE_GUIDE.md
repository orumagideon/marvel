# Marvel Trading Dashboard - Windows EXE Build Guide

## Quick Start: Build the Executable

### Option 1: Automated Build (Recommended)

On Windows, simply run:
```batch
build.bat
```

This will:
1. Check Python installation
2. Install PyInstaller if needed
3. Install all dependencies
4. Build the executable
5. Show you where the .exe is located

Expected time: 2-5 minutes

---

### Option 2: Manual Build (PowerShell)

```powershell
# Navigate to project directory
cd C:\path\to\marvel

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Build executable
pyinstaller marvel.spec

# The executable will be in: dist\Marvel\Marvel.exe
```

---

### Option 3: Manual Build (Command Prompt)

```batch
cd C:\path\to\marvel
pip install -r requirements.txt
pyinstaller marvel.spec
```

---

## What Gets Built

When you run the build, PyInstaller creates:

```
dist/
└── Marvel/
    ├── Marvel.exe ................. Your executable (run this!)
    ├── app/ ....................... Application modules
    ├── data/ ...................... Configuration files
    ├── logs/ ...................... Log directory
    └── [dependencies] ............ All required libraries
```

The `dist\Marvel` folder contains everything needed to run the dashboard. You can copy this entire folder to another Windows machine and run it there.

---

## Running the Executable

### From Windows Explorer
1. Navigate to `dist\Marvel\`
2. Double-click `Marvel.exe`
3. Dashboard launches

### From Command Line
```batch
cd dist\Marvel
Marvel.exe
```

### From Anywhere
If you add `dist\Marvel\` to your Windows PATH, you can run:
```batch
Marvel.exe
```

---

## Troubleshooting Build Issues

### Error: "python: command not found"
**Solution**: Python not installed or not in PATH
- Download Python 3.12+ from python.org
- During installation, check "Add Python to PATH"
- Restart command prompt and try again

### Error: "pyinstaller: command not found"
**Solution**: PyInstaller not installed
```batch
pip install pyinstaller
```

### Error: "MetaTrader5 not found"
**Solution**: MetaTrader5 only works on Windows
- This is expected on Linux development machines
- Build process continues anyway
- On Windows, MT5 will work normally

### Build is very slow
**Solution**: This is normal, especially first time
- Build can take 2-5 minutes
- PyInstaller is collecting all dependencies
- Subsequent builds are faster (cached)

### Executable won't start
**Possible solutions**:
1. Check that MetaTrader5 is installed on the Windows machine
2. Run from command line to see error messages:
   ```batch
   dist\Marvel\Marvel.exe
   ```
3. Check Windows Event Viewer for error details

### Build creates huge exe (>500MB)
**Normal**: This includes all Python runtime and libraries
- Marvel.exe is typically 300-500MB
- Smaller than installing full Python + all packages
- Only needed once; run multiple times from same folder

---

## Building on Different Windows Machines

### Single EXE (All-in-One)

If you want a single executable file instead of a folder:

Edit `marvel.spec` and change:
```python
# Change this:
console=False,  # Set to True if you want console window visible

# To use UPX compression:
upx=True,
```

Then rebuild:
```batch
pyinstaller marvel.spec --onefile
```

This creates `dist\Marvel.exe` (single file, but larger)

---

## Advanced Options

### Include Console Window

Edit `marvel.spec` and change:
```python
console=False,  # Change to True
```

Then rebuild. This shows a console window for debugging.

### Custom Icon

1. Get an `.ico` file for your icon
2. Place it in the project root as `app_icon.ico`
3. The spec file already references it:
   ```python
   icon='app_icon.ico',
```
4. Rebuild

### Exclude Debugging Info

Edit `marvel.spec` and change:
```python
debug=False,  # Already set
```

---

## Distributing Your Executable

### Option 1: Folder Distribution (Recommended)
Copy the entire `dist\Marvel` folder to other Windows machines
- All dependencies included
- Easier troubleshooting
- Standard approach

### Option 2: Single File Distribution
Build with `--onefile` flag
- Single executable
- Larger file size
- Easier to distribute (one file)

### Option 3: Installer (Advanced)
Use NSIS or InnoSetup to create an installer:
- Professional appearance
- Auto-installation to Program Files
- Requires additional software

---

## Post-Build Steps

### 1. Test the Executable

```batch
cd dist\Marvel
Marvel.exe
```

Verify:
- ✓ Dashboard launches
- ✓ No Python errors
- ✓ Configuration loads
- ✓ Logging works

### 2. Verify All Features

- [ ] Dashboard UI appears
- [ ] Status indicators show
- [ ] Configuration loads
- [ ] Logs are created
- [ ] No errors in output

### 3. Deploy to VPS

1. Copy entire `dist\Marvel` folder to your Windows VPS
2. On the VPS, run:
   ```batch
   Marvel.exe
   ```
3. Configure MetaTrader5 paths (first run)
4. Add your accounts
5. Start trading!

---

## Size Optimization

Default build: ~400-500MB

To reduce size:

### Option 1: Exclude Unused Modules

Edit `marvel.spec`, in the `excludedimports` list:
```python
excludedimports=[
    'tkinter',           # If not using Tkinter
    'numpy',             # If not using NumPy
    'matplotlib',        # If not using Matplotlib
]
```

### Option 2: Use UPX Compression

UPX is already enabled in `marvel.spec`:
```python
upx=True,
```

### Option 3: Strip Debugging Info

Already enabled:
```python
strip=False,  # Change to True for smaller but less debuggable exe
```

---

## Rebuilding After Code Changes

If you modify the Python code:

```batch
# Just rebuild (files cached)
pyinstaller marvel.spec

# Clean rebuild
pyinstaller marvel.spec --clean
```

Clean rebuilds are slower but ensure everything is fresh.

---

## Files Reference

| File | Purpose |
|------|---------|
| `marvel.spec` | PyInstaller configuration |
| `build.bat` | Automated Windows build script |
| `build_spec.py` | Additional build options |
| `main.py` | Entry point for executable |
| `dist/Marvel/` | Output folder with executable |

---

## Next Steps

1. **Build**: Run `build.bat`
2. **Test**: Run `dist\Marvel\Marvel.exe`
3. **Configure**: Set up MetaTrader5 paths
4. **Deploy**: Copy to your Windows VPS
5. **Run**: Start trading!

---

## Support

If you encounter issues:

1. Check troubleshooting section above
2. Verify Python 3.12+ installed
3. Verify all dependencies: `pip install -r requirements.txt`
4. Run with verbose output: `pyinstaller marvel.spec -v`
5. Check build logs in `build` folder

---

**Last Updated**: 2026-05-10  
**Status**: ✅ Ready for Windows executable build
