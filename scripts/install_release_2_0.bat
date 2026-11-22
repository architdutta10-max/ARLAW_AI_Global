@echo off
setlocal EnableExtensions

REM Guarded integration: preserves Git metadata, secrets, local data and virtual environments.
set "SOURCE=%~dp0.."
for %%I in ("%SOURCE%") do set "SOURCE=%%~fI"
set "PROJECT=%~1"
if "%PROJECT%"=="" set "PROJECT=%USERPROFILE%\OneDrive\Desktop\ARLAW_AI_Global"
for %%I in ("%PROJECT%") do set "PROJECT=%%~fI"
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%I"
set "BACKUP=%PROJECT%_backup_%STAMP%"

echo ==================================================
echo ARLAW AI Global 2.0 - guarded integration
echo Source:  %SOURCE%
echo Target:  %PROJECT%
echo Backup:  %BACKUP%
echo ==================================================

if not exist "%SOURCE%\app\main.py" (echo ERROR: Release source not found.& exit /b 1)
if not exist "%SOURCE%\app\static\index.html" (echo ERROR: Frontend files missing.& exit /b 1)
if not exist "%PROJECT%\.git" (echo ERROR: Target is not an existing Git repository.& exit /b 1)
where git >nul 2>nul || (echo ERROR: Git is not installed or not on PATH.& exit /b 1)
where py >nul 2>nul || (echo ERROR: Python launcher 'py' not found.& exit /b 1)

cd /d "%PROJECT%" || exit /b 1
for /f "delims=" %%B in ('git branch --show-current') do set "BRANCH=%%B"
if not defined BRANCH (echo ERROR: Detached HEAD. Switch to your intended branch first.& exit /b 1)
git status --porcelain > "%TEMP%\arlaw_git_status.txt"
for %%A in ("%TEMP%\arlaw_git_status.txt") do if %%~zA GTR 0 (
  echo ERROR: Working tree is not clean. Commit or back up your changes first.
  type "%TEMP%\arlaw_git_status.txt"
  del "%TEMP%\arlaw_git_status.txt"
  exit /b 1
)
del "%TEMP%\arlaw_git_status.txt"

echo Current branch: %BRANCH%
echo Confirm that this is the intended repository and branch:
git remote -v
choice /C YN /M "Continue and create a full backup first"
if errorlevel 2 exit /b 1
if exist "%BACKUP%" (echo ERROR: Backup path already exists.& exit /b 1)

robocopy "%PROJECT%" "%BACKUP%" /E /XD .git .venv venv __pycache__ .pytest_cache data /XF .env
if errorlevel 8 (echo ERROR: Backup failed. No integration performed.& exit /b 1)
robocopy "%SOURCE%" "%PROJECT%" /E /XD .git .venv venv __pycache__ .pytest_cache data /XF .env
if errorlevel 8 (echo ERROR: Copy failed. Restore from backup if necessary.& exit /b 1)

cd /d "%PROJECT%" || exit /b 1
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt pytest
if errorlevel 1 exit /b 1
python -m pytest -q
if errorlevel 1 (echo ERROR: Tests failed. Do not commit or push.& exit /b 1)
git diff --check
if errorlevel 1 exit /b 1

echo.
echo SUCCESS: Release 2.0 integrated and automated tests passed.
echo Backup: %BACKUP%
echo Review changes with: git status and git diff
echo No commit or push was performed.
endlocal
