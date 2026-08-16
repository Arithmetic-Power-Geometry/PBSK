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
py -3.12 -m pbsk.cli full --config config/default.yaml
if errorlevel 1 goto :err
start "" "%CD%\results\PBSK_RESULTS.html"
exit /b 0
:err
echo PBSK full run failed. Check the console output and configured environment variables.
pause
exit /b 1
