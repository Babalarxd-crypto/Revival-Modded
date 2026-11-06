@echo off
cd /d "%~dp0"
"Python\python.exe" limited_run.py "Python\python.exe" roster_launcher.py
if errorlevel 1 pause
