@echo off
setlocal enableextensions enabledelayedexpansion

REM Change to script directory (project root)
pushd "%~dp0"

REM Ensure entry script exists
if not exist "src\gengif.py" (
  echo Error: entry script `src\gengif.py` not found in project root.
  popd
  exit /b 1
)

REM Venv selection: prefer active venv, otherwise .venv
set "VENV=.venv"
if defined VIRTUAL_ENV (
  set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
) else (
  set "PY=%VENV%\Scripts\python.exe"
)

REM Create venv if missing
if not exist "%PY%" (
  echo Creating virtual environment...
  py -3 -m venv "%VENV%" 2>nul || python -m venv "%VENV%"
  if exist "%VENV%\Scripts\python.exe" (
    set "PY=%VENV%\Scripts\python.exe"
  ) else (
    echo Error: failed to create virtual environment.
    popd
    exit /b 1
  )
)

REM Upgrade pip and install dependencies
echo Installing build dependencies...
"%PY%" -m pip install --upgrade pip >nul
if exist "requirements.txt" (
  "%PY%" -m pip install -r requirements.txt
) else (
  "%PY%" -m pip install pyinstaller opencv-contrib-python numpy imageio pillow
)

REM Clean previous PyInstaller artifacts
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist
if exist gengif.spec del /q gengif.spec

REM Build single-file exe; bundle gengif.ini alongside the exe
echo Building gengif.exe...
"%PY%" -m PyInstaller --noconfirm --clean --onefile --name gengif ^
  --copy-metadata imageio ^
  --add-data "gengif.ini;." ^
  "src\gengif.py"

REM Optional: also bundle test images folder for offline tests
REM Add this to the command above if needed:
REM   --add-data "testdata\img3;testdata\img3"

REM Report result
if exist "dist\gengif.exe" (
  for %%F in ("dist\gengif.exe") do echo Built: %%~fF
  popd
  exit /b 0
) else (
  echo Error: build failed. Check PyInstaller output above.
  popd
  exit /b 1
)
