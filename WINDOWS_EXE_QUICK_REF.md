# 🚀 MARVEL WINDOWS EXE - QUICK REFERENCE

## ⚡ FASTEST WAY TO BUILD

```
1. Copy /marvel folder to Windows:   C:\marvel
2. Open Command Prompt in C:\marvel
3. Run:                             build.bat
4. Wait 2-5 minutes
5. Run executable:                  dist\Marvel\Marvel.exe
```

**That's it!** Your executable is ready.

---

## 📋 WHAT'S IN THE BOX

You have everything you need to create your .exe:

```
marvel/
├── marvel.spec .............. Build configuration ✓
├── build.bat ................ Build script (Windows) ✓
├── build.ps1 ................ Build script (PowerShell) ✓
├── requirements.txt ......... Dependencies ✓
├── main.py .................. Entry point ✓
├── app/ ..................... Source code (22 files) ✓
├── data/ .................... Configuration ✓
└── logs/ .................... Log directory ✓
```

---

## 🎯 QUICK STEPS

### Step 1: Copy to Windows
Copy the entire `/marvel` folder to your Windows machine
```
C:\Users\YourName\Documents\marvel
```

### Step 2: Build (Choose ONE)

#### Easiest: Use Batch Script
```batch
cd C:\Users\YourName\Documents\marvel
build.bat
```

#### Alternative: Use PowerShell
```powershell
cd C:\Users\YourName\Documents\marvel
.\build.ps1
```

#### Manual: Command Line
```batch
cd C:\Users\YourName\Documents\marvel
pip install -r requirements.txt
pyinstaller marvel.spec
```

### Step 3: Find Your Executable
```
C:\Users\YourName\Documents\marvel\dist\Marvel\Marvel.exe
```

### Step 4: Run It!
```batch
Double-click: Marvel.exe
Or from command line: Marvel.exe
```

---

## 📊 BUILD OUTPUT

After successful build, you'll have:

```
dist\Marvel\
├── Marvel.exe (15-20 MB) ......... YOUR EXECUTABLE ✓
├── app\ ......................... Application code
├── data\ ........................ Configuration files
├── logs\ ........................ Log directory
└── _internal\ (350-400 MB) ...... All Python libraries
```

**Total size: ~400-500 MB**

This is normal! It includes all Python and all dependencies.

---

## ⏱️ TIMING

| Step | Time |
|------|------|
| Copy to Windows | 1-2 min |
| Build | 2-5 min |
| Test run | 1 min |
| **Total** | **5-10 min** |

---

## ✅ TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| `Python not found` | Install Python 3.12+, add to PATH |
| `build.bat doesn't run` | Right-click → Run as Administrator |
| `Build takes forever` | Normal first time, takes 2-5 min |
| `MetaTrader5 error` | Normal on build machine, will work on Windows |
| `.exe won't launch` | Run from CMD to see errors |

---

## 🔄 REBUILD AFTER CODE CHANGES

If you modify the Python code:

```batch
# Just rebuild
pyinstaller marvel.spec

# Or clean rebuild
pyinstaller marvel.spec --clean
```

---

## 📚 FULL GUIDES

If you need more details:

- **[CREATE_WINDOWS_EXE.md](CREATE_WINDOWS_EXE.md)** ← Start here
- **[BUILD_EXE_GUIDE.md](BUILD_EXE_GUIDE.md)** ← Detailed instructions

---

## 🎯 ONE-COMMAND BUILD

Just run this from command prompt in the marvel folder:

```batch
build.bat
```

That's literally all you need to type!

---

## ✨ DEPLOY YOUR EXE

Once built, you can:

1. **Run locally** - Double-click `Marvel.exe`
2. **Copy to USB** - Give to others on Windows
3. **Copy to VPS** - Deploy to production
4. **Create shortcut** - Right-click → Create shortcut

---

**Status**: ✅ BUILD FILES READY - Go to Windows and run `build.bat`
