@echo off
rem Starts Photo Finder Pro from source (development). One window at a time.
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
"%~dp0venv\Scripts\pythonw.exe" -m photofinder
