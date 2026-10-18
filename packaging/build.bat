@echo off
setlocal
rem One command builds everything: onedir -> selftest -> onefile -> selftest -> installer (if Inno Setup 6 is found).
rem Outputs: dist\PhotoFinderPro-Setup-<ver>.exe  and  dist\PhotoFinderPro-<ver>-Portable.exe. Run from anywhere.
set ROOT=%~dp0..
pushd "%ROOT%"
set PY=venv\Scripts\python.exe
set VER=1.0.0
set REPORT=%TEMP%\photofinderpro_selftest.txt
set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

"%PY%" packaging\make_icon.py || goto :fail

echo === [1/3] onedir build ===
"%PY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build\onedir packaging\photofinderpro.spec || goto :fail
call :selftest "dist\PhotoFinderPro\PhotoFinderPro.exe" || goto :fail

echo === [2/3] onefile (portable) build ===
"%PY%" -m PyInstaller --noconfirm --distpath dist --workpath build\onefile packaging\photofinderpro_onefile.spec || goto :fail
call :selftest "dist\PhotoFinderPro-%VER%-Portable.exe" || goto :fail

echo === [3/3] installer ===
if "%ISCC%"=="" (
  echo Inno Setup 6 not found - skipping installer. Install: winget install --id JRSoftware.InnoSetup -e
) else (
  "%ISCC%" packaging\installer.iss || goto :fail
)

echo.
echo Build OK. Outputs:
if exist "dist\PhotoFinderPro-Setup-%VER%.exe" echo   %CD%\dist\PhotoFinderPro-Setup-%VER%.exe
echo   %CD%\dist\PhotoFinderPro-%VER%-Portable.exe
popd
exit /b 0

:selftest
if exist "%REPORT%" del "%REPORT%"
start /wait "" %1 --selftest
set RC=%ERRORLEVEL%
if not exist "%REPORT%" (echo Selftest wrote no report & exit /b 1)
type "%REPORT%"
findstr /c:"RESULT: OK" "%REPORT%" >nul || (echo Selftest FAILED & exit /b 1)
if not "%RC%"=="0" (echo Selftest exit code %RC% & exit /b 1)
exit /b 0

:fail
echo BUILD FAILED
popd
exit /b 1
