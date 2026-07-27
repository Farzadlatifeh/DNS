# How to Build DNS_Manager.exe using PyInstaller

This guide explains how to create a standalone `.exe` file for the DNS Manager GUI application that preserves all functionalities.

## Prerequisites

1. **Windows 10/11** - This application is designed for Windows and uses Windows-specific APIs
2. **Python 3.8 or higher** installed
3. **All required packages** installed:
   ```bash
   pip install PyQt6 qt-material pyinstaller
   ```

## Method 1: Using the Spec File (Recommended)

The project includes a pre-configured `dns_manager.spec` file that contains all necessary settings.

### Steps:

1. **Open Command Prompt or PowerShell** as Administrator (recommended for testing)

2. **Navigate to the project directory:**
   ```cmd
   cd path\to\your\project
   ```

3. **Run PyInstaller with the spec file:**
   ```cmd
   pyinstaller --clean dns_manager.spec
   ```

4. **Wait for the build to complete** (may take 1-2 minutes)

5. **Find your .exe file** in the `dist` folder:
   - `dist/DNS_Manager.exe` - Your standalone executable

## Method 2: One-Line Command

If you prefer a quick build without the spec file:

```cmd
pyinstaller --onefile --windowed --name DNS_Manager --add-data "dns_profiles.json;." --add-data "extract_dns.py;." --hidden-import=PyQt6 --hidden-import=qt_material dns_manager_gui.py
```

## Important Notes

### ⚠️ Running on Linux/Mac
The current environment is Linux, which will produce a **Linux executable**, not a Windows `.exe`. To create a Windows `.exe`:
- You must run PyInstaller on **Windows**
- Or use a Windows VM/container
- Or use cross-compilation tools (more complex)

### Included Files
The spec file ensures these files are bundled:
- `dns_profiles.json` - DNS profile database
- `extract_dns.py` - Script for refreshing DNS profiles

### Features Preserved
The built `.exe` maintains all functionalities:
- ✅ PyQt6 GUI interface
- ✅ DNS profile loading from JSON
- ✅ Ping testing in background threads
- ✅ DNS profile application to network adapters
- ✅ Profile reloading via extract_dns.py
- ✅ Reset to DHCP functionality
- ✅ Administrator privilege detection
- ✅ qt-material dark theme (if available)

## Distribution

To distribute your application:

1. **Share the entire `dist` folder** or just `DNS_Manager.exe`
2. **Users don't need Python installed** - it's fully standalone
3. **First run may trigger Windows Defender** - this is normal for PyInstaller apps
4. **Consider code signing** for production distribution to avoid security warnings

## Troubleshooting

### Missing DLL errors
Make sure all dependencies are installed:
```cmd
pip install --upgrade PyQt6 qt-material pyinstaller
```

### Application won't start
Try running with console output to see errors:
```cmd
# In the spec file, change: console=False to console=True
# Then rebuild
```

### Antivirus flags the .exe
This is a common false positive with PyInstaller apps. Options:
- Sign your executable with a code signing certificate
- Add an exception in antivirus software
- Report the false positive to the antivirus vendor

### Large file size
The single-file executable is ~50-100MB due to:
- Python runtime embedding
- PyQt6 libraries
- Qt dependencies

To reduce size:
- Use `--onedir` instead of `--onefile` (creates a folder with smaller individual files)
- Remove unused modules in the spec file

## Custom Icon

To add a custom icon:

1. Get a `.ico` file (e.g., `app_icon.ico`)
2. Update the spec file:
   ```python
   exe = EXE(
       ...
       icon='app_icon.ico',
       ...
   )
   ```
3. Rebuild: `pyinstaller --clean dns_manager.spec`

## Quick Reference

| Command | Description |
|---------|-------------|
| `pyinstaller --clean dns_manager.spec` | Build using spec file |
| `pyinstaller --onefile --windowed dns_manager_gui.py` | Quick build (basic) |
| `rm -rf build dist *.spec` | Clean all build artifacts |

## Support

For issues related to:
- **PyInstaller**: https://github.com/pyinstaller/pyinstaller/issues
- **PyQt6**: https://www.riverbankcomputing.com/support/
- **This application**: Check the project's issue tracker
