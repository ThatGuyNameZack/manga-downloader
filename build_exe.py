"""
Build script for creating optimized EXE
Run this script to build your manga downloader
"""

import subprocess
import sys
import os

def build_with_pyinstaller():
    """Build using PyInstaller (recommended)"""
    cmd = [
        'pyinstaller',
        '--onefile',           # Single executable file
        '--windowed',          # No console window
        '--optimize=2',        # Optimize Python bytecode
        '--strip',            # Strip symbols from executable
        '--clean',            # Clean cache before building
        '--name=MangaDownloader',  # Name of the executable
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        '--exclude-module=tkinter',  # We're using PyQt5 now
        
        # Include only necessary Qt modules
        '--hidden-import=PyQt5.sip',
        
        # Add icon if you have one
        # '--icon=icon.ico',
        
        'main.py'  # Your main Python file
    ]
    
    print("Building with PyInstaller...")
    print("Command:", ' '.join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print("Executable created in 'dist/' folder")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def build_with_cx_freeze():
    """Alternative build using cx_Freeze"""
    
    # Create setup.py for cx_Freeze
    setup_content = '''
from cx_Freeze import setup, Executable
import sys

# Dependencies are automatically detected, but it might need fine tuning.
build_options = {
    'packages': ['PyQt5', 'requests', 'json', 'os', 'threading'],
    'excludes': ['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    'include_files': [],
    'optimize': 2,
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('main.py', base=base, target_name='MangaDownloader.exe')
]

setup(
    name='MangaDownloader',
    version='1.0',
    description='Manga Downloader Application',
    options={'build_exe': build_options},
    executables=executables
)
'''
    
    with open('setup_cx.py', 'w') as f:
        f.write(setup_content)
    
    cmd = [sys.executable, 'setup_cx.py', 'build']
    
    print("Building with cx_Freeze...")
    try:
        result = subprocess.run(cmd, check=True)
        print("Build successful!")
        print("Executable created in 'build/' folder")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def check_dependencies():
    """Check if required tools are installed"""
    try:
        import PyQt5
        print("✓ PyQt5 found")
    except ImportError:
        print("✗ PyQt5 not found. Install with: pip install PyQt5")
        return False
    
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        print("✓ PyInstaller found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ PyInstaller not found. Install with: pip install pyinstaller")
        
        # Check for cx_Freeze as alternative
        try:
            import cx_Freeze
            print("✓ cx_Freeze found as alternative")
            return True
        except ImportError:
            print("✗ cx_Freeze not found either. Install with: pip install cx_Freeze")
            return False

def main():
    print("Manga Downloader Build Script")
    print("=" * 40)
    
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        return
    
    print("\nChoose build method:")
    print("1. PyInstaller (recommended)")
    print("2. cx_Freeze (alternative)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        success = build_with_pyinstaller()
    elif choice == '2':
        success = build_with_cx_freeze()
    else:
        print("Invalid choice")
        return
    
    if success:
        print("\n" + "=" * 40)
        print("BUILD SUCCESSFUL!")
        print("Your manga downloader is ready to use.")
        print("The executable file is optimized and should run much faster.")
    else:
        print("\nBuild failed. Please check the error messages above.")

if __name__ == "__main__":
    main()