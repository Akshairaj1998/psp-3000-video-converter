@echo off
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Launching PSP 3000 Video Converter...
python main.py
