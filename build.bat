@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building PSP 3000 Video Converter.exe ...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "PSP 3000 Video Converter" ^
  --add-data "ui;ui" ^
  main.py

echo.
echo Build complete! Find the exe in the dist\ folder.
pause
