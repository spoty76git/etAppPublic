import PyInstaller.__main__
import os

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',
    '--onefile',            # Single executable
    #'--noconsole',          # No console window
    '--name=MyDashApp',     # Output name
    '--add-data=assets;assets',  # Include static files
    '--hidden-import=waitress',
    '--hidden-import=dash',
    '--hidden-import=flask',
    '--clean'               # Clean build
])