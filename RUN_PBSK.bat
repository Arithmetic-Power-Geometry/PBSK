@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m pip install --upgrade pip
if errorlevel 1 goto :err
py -3.12 -m pip install -r requirements.txt
if errorlevel 1 goto :err
py -3.12 -m pip install -e .
if errorlevel 1 goto :err
py -3.12 -m pytest -q
if errorlevel 1 goto :err
py -3.12 -m pbsk.cli smoke --config config/default.yaml
if errorlevel 1 goto :err
start "" "%CD%\results\smoke_report.json"
exit /b 0
:err
echo PBSK smoke run failed.
pause
exit /b 1
