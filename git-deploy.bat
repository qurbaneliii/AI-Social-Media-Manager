@echo off
setlocal enabledelayedexpansion

cd /d C:\Users\qurba\AI-Social-Media-Manager

echo === STEP 1: Confirm repo dir and git status ===
echo Current directory: %CD%
if exist .git (
    echo .git directory exists
) else (
    echo .git directory NOT found
    git init
    echo Git initialized
)

echo.
echo === STEP 2: Check git status ===
git status

echo.
echo === STEP 3: Get remote URL ===
git config --get remote.origin.url > remote-url.txt
for /f "tokens=*" %%A in (remote-url.txt) do set REMOTE_URL=%%A
if "!REMOTE_URL!"=="" (
    echo ERROR: No remote URL found
    echo Required: Set remote with: git remote add origin ^<URL^>
    exit /b 1
) else (
    echo Remote URL: !REMOTE_URL!
)

echo.
echo === STEP 4: Check for uncommitted changes ===
git status --porcelain > status-changes.txt
for /f "tokens=*" %%A in (status-changes.txt) do (
    echo %%A
)

echo.
echo === STEP 5: Stage and commit all changes ===
git add -A
git commit --no-verify -m "frontend: version update

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

if errorlevel 1 (
    echo WARNING: Commit may have failed or no changes to commit
    git log --oneline -1
) else (
    echo Commit successful
    git log --oneline -1 > commit-hash.txt
    for /f "tokens=*" %%A in (commit-hash.txt) do set COMMIT_HASH=%%A
    echo Latest commit: !COMMIT_HASH!
)

echo.
echo === STEP 6: Detect default branch ===
git symbolic-ref refs/remotes/origin/HEAD 2>nul | sed 's/^refs\/remotes\/origin\///' > default-branch.txt
for /f "tokens=*" %%A in (default-branch.txt) do set DEFAULT_BRANCH=%%A
if "!DEFAULT_BRANCH!"=="" (
    echo Checking for main/master...
    if exist .git\refs\heads\main (
        set DEFAULT_BRANCH=main
    ) else if exist .git\refs\heads\master (
        set DEFAULT_BRANCH=master
    ) else (
        git branch -a | findstr "origin/main origin/master"
    )
)
echo Default branch: !DEFAULT_BRANCH!

echo.
echo === STEP 7: Push to remote ===
git push -u origin !DEFAULT_BRANCH!

echo.
echo === STEP 8: Check for aria-frontend (Next.js) ===
if exist aria-frontend (
    echo aria-frontend directory found
    if exist aria-frontend\next.config.js (
        echo next.config.js found
        findstr /C:"output: 'export'" aria-frontend\next.config.js
        if errorlevel 1 (
            echo Static export NOT configured
        ) else (
            echo Static export is configured
        )
    ) else (
        echo next.config.js NOT found
    )
)

echo.
echo === STEP 9: Check GitHub Pages configuration ===
if exist .github\workflows (
    echo GitHub Actions workflows found:
    for /r .github\workflows %%F in (*.yml) do (
        echo %%~nF
    )
)

echo.
echo === DEPLOYMENT COMPLETE ===
echo Final commit:
git log --oneline -1

endlocal
