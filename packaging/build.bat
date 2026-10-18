@echo off
setlocal
rem Builds dist\PhotoFinderPro (onedir), checks it with --selftest, zips it. Run from anywhere.
set ROOT=%~dp0..
pushd "%ROOT%"
set PY=venv\Scripts\python.exe
set VER=1.0.0
set REPORT=%TEMP%\photofinderpro_selftest.txt

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

"%PY%" packaging\make_icon.py || goto :fail
"%PY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\photofinderpro.spec || goto :fail

if exist "%REPORT%" del "%REPORT%"
start /wait "" "dist\PhotoFinderPro\PhotoFinderPro.exe" --selftest
set RC=%ERRORLEVEL%
if not exist "%REPORT%" (echo Selftest wrote no report & goto :fail)
type "%REPORT%"
findstr /c:"RESULT: OK" "%REPORT%" >nul || (echo Selftest FAILED & goto :fail)
if not "%RC%"=="0" (echo Selftest exit code %RC% & goto :fail)

powershell -NoProfile -Command "Compress-Archive -Path 'dist\PhotoFinderPro' -DestinationPath 'dist\PhotoFinderPro-%VER%-win64.zip' -Force" || goto :fail
echo.
echo Build OK: dist\PhotoFinderPro-%VER%-win64.zip
popd
exit /b 0

:fail
echo BUILD FAILED
popd
exit /b 1
