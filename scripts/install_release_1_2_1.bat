@echo off
setlocal EnableExtensions

REM Run from the extracted release folder or pass the existing project path.
set "SOURCE=%~dp0.."
for %%I in ("%SOURCE%") do set "SOURCE=%%~fI"
set "PROJECT=%~1"
if "%PROJECT%"=="" set "PROJECT=%USERPROFILE%\OneDrive\Desktop\ARLAW_AI_Global"
for %%I in ("%PROJECT%") do set "PROJECT=%%~fI"
set "STAMP=%DATE:/=-%_%TIME::=-%"
set "STAMP=%STAMP: =0%"
set "BACKUP=%PROJECT%_backup_%STAMP%"

echo ==================================================
echo ARLAW AI Global - guarded local integration
echo Source:  %SOURCE%
echo Target:  %PROJECT%
echo Backup:  %BACKUP%
echo ==================================================

if not exist "%SOURCE%\app\main.py" (echo ERROR: Release source folder not found.& exit /b 1)
if not exist "%SOURCE%\app\static\index.html" (echo ERROR: Frontend files missing.& exit /b 1)
if not exist "%PROJECT%\.git" (echo ERROR: Target is not an existing Git repository.& exit /b 1)

where git >nul 2>nul || (echo ERROR: Git is not installed or not on PATH.& exit /b 1)
where py >nul 2>nul || (echo ERROR: Python launcher 'py' not found.& exit /b 1)

cd /d "%PROJECT%" || exit /b 1
for /f "delims=" %%B in ('git branch --show-current') do set "BRANCH=%%B"
if not defined BRANCH (echo ERROR: Detached HEAD. Switch to your intended branch first.& exit /b 1)

git status --porcelain > "%TEMP%\arlaw_git_status.txt"
for %%A in ("%TEMP%\arlaw_git_status.txt") do if %%~zA GTR 0 (
  echo ERROR: Working tree is not clean. Commit or back up your work first.
  type "%TEMP%\arlaw_git_status.txt"
  del "%TEMP%\arlaw_git_status.txt"
  exit /b 1
)
del "%TEMP%\arlaw_git_status.txt"

echo.
echo Current branch: %BRANCH%
echo Review this branch and remote before continuing.
git remote -v
choice /C YN /M "Continue after confirming this is the intended branch and remote"
if errorlevel 2 exit /b 1

if exist "%BACKUP%" (echo ERROR: Backup path already exists.& exit /b 1)
robocopy "%PROJECT%" "%BACKUP%" /E /XD .git .venv venv __pycache__ data /XF .env
if errorlevel 8 (echo ERROR: Backup failed.& exit /b 1)

REM Preserve Git metadata, local secrets, virtual environments and user data.
robocopy "%SOURCE%" "%PROJECT%" /E /XD .git .venv venv __pycache__ data /XF .env
if errorlevel 8 (echo ERROR: File integration failed. Restore from backup if needed.& exit /b 1)

cd /d "%PROJECT%"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 (echo ERROR: Dependency installation failed.& exit /b 1)
python -m pip install pytest
if errorlevel 1 exit /b 1
python -m pytest -q
if errorlevel 1 (echo ERROR: Tests failed. Do not commit or push.& exit /b 1)
git diff --check
if errorlevel 1 exit /b 1

echo.
echo SUCCESS: Local integration and automated checks passed.
echo Backup: %BACKUP%
echo Review with: git status and git diff
 echo No commit or push was performed.
endlocal
