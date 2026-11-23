@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==================================================
echo  ARLAW AI Global 2.3.0 - GitHub release push
echo ==================================================

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo ERROR: This folder is not inside a Git repository.
  echo Extract the release ZIP into your existing ARLAW_AI_Global checkout first.
  pause
  exit /b 1
)

for %%F in (.env .env.local) do (
  git ls-files --error-unmatch "%%F" >nul 2>&1
  if not errorlevel 1 (
    echo ERROR: %%F is tracked by Git. Remove secrets from tracking before pushing.
    echo Run: git rm --cached %%F
    pause
    exit /b 1
  )
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo ERROR: Git remote 'origin' is not configured.
  echo Configure it with: git remote add origin YOUR_REPOSITORY_URL
  pause
  exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current') do set "BRANCH=%%B"
if not defined BRANCH (
  echo ERROR: Could not determine the current Git branch.
  pause
  exit /b 1
)

echo.
echo Current branch: %BRANCH%
echo Remote:
git remote -v

echo.
echo Current working-tree changes:
git status --short

echo.
echo IMPORTANT: Check the list above. Confirm .env, API keys, .venv and private data are NOT staged.
choice /M "Continue to stage all tracked project changes"
if errorlevel 2 exit /b 0

git add -A
if errorlevel 1 goto :failed

git diff --cached --check
if errorlevel 1 (
  echo ERROR: Whitespace/conflict-marker check failed. Review the staged diff.
  pause
  exit /b 1
)

git diff --cached --quiet
if not errorlevel 1 (
  echo No staged changes. Nothing to commit; checking push status.
) else (
  echo.
  git diff --cached --stat
  echo.
  choice /M "Commit these staged changes"
  if errorlevel 2 exit /b 0
  git commit -m "Release ARLAW AI Global 2.3.0"
  if errorlevel 1 goto :failed
)

echo.
echo Pushing branch %BRANCH% to origin...
git push -u origin "%BRANCH%"
if errorlevel 1 goto :failed

echo.
echo Push command completed. Final Git status:
git status --short
 echo.
echo Done. Verify the commit and GitHub Actions result on GitHub.
pause
exit /b 0

:failed
echo.
echo ERROR: A Git command failed. No success is being claimed.
echo Review the output above, correct the issue, and run this file again.
pause
exit /b 1
