@echo off
rem Excel-Datei(en) mit der Maus auf diese Datei ziehen: erzeugt das PDF neben der Excel-Datei.
rem Voraussetzung: Installation nach docs/Installation.md (Python, LuaLaTeX, vfdb-stil).
chcp 65001 >nul
if "%~1"=="" (
  echo Bitte eine Excel-Datei mit der Maus auf diese Datei ziehen.
  pause
  exit /b 1
)
python -m vfdb_stil.excel %*
echo.
pause
