@echo off
setlocal
rem One command builds everything (64-bit x64): onedir -> selftest -> zip -> onefile -> selftest -> installer (if Inno Setup 6 is found).
rem Outputs in dist\: PhotoFinderPro-<ver>-x64-Setup.exe, PhotoFinderPro-<ver>-x64-Portable.exe, PhotoFinderPro-<ver>-x64.zip
rem and SHA256SUMS.txt. Run from anywhere. Other files in dist\ (e.g. MSIX packages) are left alone.
set ROOT=%~dp0..
pushd "%ROOT%"
set PY=venv\Scripts\python.exe
set VER=1.0.1
set REPORT=%TEMP%\photofinderpro_selftest.txt
set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if exist build rmdir /s /q build
if exist dist\PhotoFinderPro rmdir /s /q dist\PhotoFinderPro
for %%F in ("dist\PhotoFinderPro-%VER%-x64-*" "dist\SHA256SUMS.txt") do if exist %%F del /q %%F

"%PY%" packaging\make_icon.py || goto :fail

echo === [1/4] onedir build ===
"%PY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build\onedir packaging\photofinderpro.spec || goto :fail
call :selftest "dist\PhotoFinderPro\PhotoFinderPro.exe" || goto :fail

echo === [2/4] zip of the onedir folder ===
if exist "dist\PhotoFinderPro-%VER%-x64.zip" del "dist\PhotoFinderPro-%VER%-x64.zip"
rem Windows' own tar (bsdtar) writes a standard zip; Compress-Archive in PowerShell 5.1 stores backslash paths.
"%SystemRoot%\System32\tar.exe" -a -c -f "dist\PhotoFinderPro-%VER%-x64.zip" -C dist PhotoFinderPro || goto :fail

echo === [3/4] onefile (portable) build ===
"%PY%" -m PyInstaller --noconfirm --distpath dist --workpath build\onefile packaging\photofinderpro_onefile.spec || goto :fail
call :selftest "dist\PhotoFinderPro-%VER%-x64-Portable.exe" || goto :fail

echo === [4/4] installer ===
if "%ISCC%"=="" (
  echo Inno Setup 6 not found - skipping installer. Install: winget install --id JRSoftware.InnoSetup -e
) else (
  "%ISCC%" packaging\installer.iss || goto :fail
)

echo === checksums ===
powershell -NoProfile -Command "$n='PhotoFinderPro-%VER%-x64-Setup.exe','PhotoFinderPro-%VER%-x64-Portable.exe','PhotoFinderPro-%VER%-x64.zip'; $n | Where-Object { Test-Path (Join-Path 'dist' $_) } | ForEach-Object { (Get-FileHash (Join-Path 'dist' $_) -Algorithm SHA256).Hash.ToLower() + '  ' + $_ } | Set-Content -Encoding ascii dist\SHA256SUMS.txt" || goto :fail

echo.
echo Build OK. Outputs:
if exist "dist\PhotoFinderPro-%VER%-x64-Setup.exe" echo   %CD%\dist\PhotoFinderPro-%VER%-x64-Setup.exe
echo   %CD%\dist\PhotoFinderPro-%VER%-x64-Portable.exe
echo   %CD%\dist\PhotoFinderPro-%VER%-x64.zip
echo   %CD%\dist\SHA256SUMS.txt
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
