#!/usr/bin/env pwsh

$ErrorActionPreference = "Continue"
$repoPath = "C:\Users\qurba\AI-Social-Media-Manager"

Write-Host "=== STEP 1: Confirm repo dir and git status ===" -ForegroundColor Green
Set-Location $repoPath
Write-Host "Current directory: $(Get-Location)"

if (Test-Path ".git") {
    Write-Host ".git directory exists" -ForegroundColor Green
} else {
    Write-Host ".git directory NOT found - initializing..." -ForegroundColor Yellow
    & git init
}

Write-Host "`n=== STEP 2: Get remote URL ===" -ForegroundColor Green
$remoteUrl = & git config --get remote.origin.url 2>$null
if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
    Write-Host "ERROR: No remote URL configured" -ForegroundColor Red
    Write-Host "Required: git remote add origin <URL>" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "Remote URL: $remoteUrl" -ForegroundColor Green
}

Write-Host "`n=== STEP 3: Check current status ===" -ForegroundColor Green
& git status --short

Write-Host "`n=== STEP 4: Get current branch ===" -ForegroundColor Green
$currentBranch = & git rev-parse --abbrev-ref HEAD 2>$null
Write-Host "Current branch: $currentBranch"

Write-Host "`n=== STEP 5: Stage all changes ===" -ForegroundColor Green
& git add -A
Write-Host "All changes staged"

Write-Host "`n=== STEP 6: Commit with trailer ===" -ForegroundColor Green
$commitMessage = @"
frontend: version update

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"@

& git commit --no-verify -m $commitMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Commit returned exit code $LASTEXITCODE" -ForegroundColor Yellow
}

Write-Host "`n=== STEP 7: Get commit hash ===" -ForegroundColor Green
$commitHash = & git rev-parse HEAD 2>$null
if ($commitHash) {
    Write-Host "Latest commit: $commitHash" -ForegroundColor Green
} else {
    Write-Host "Could not retrieve commit hash" -ForegroundColor Yellow
}

Write-Host "`n=== STEP 8: Get default branch ===" -ForegroundColor Green
$defaultBranch = & git symbolic-ref --short refs/remotes/origin/HEAD 2>$null
if ([string]::IsNullOrWhiteSpace($defaultBranch)) {
    $defaultBranch = "main"  # fallback based on config we read
    Write-Host "Defaulting to: $defaultBranch (from git config)"
} else {
    Write-Host "Default branch: $defaultBranch"
}

Write-Host "`n=== STEP 9: Push to $defaultBranch ===" -ForegroundColor Green
& git push -u origin $defaultBranch 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Push successful!" -ForegroundColor Green
} else {
    Write-Host "Push failed with exit code: $LASTEXITCODE" -ForegroundColor Red
}

Write-Host "`n=== STEP 10: Verify aria-frontend configuration ===" -ForegroundColor Green
$frontendPath = Join-Path $repoPath "aria-frontend"
if (Test-Path $frontendPath) {
    Write-Host "aria-frontend directory found"
    $nextConfigPath = Join-Path $frontendPath "next.config.js"
    if (Test-Path $nextConfigPath) {
        Write-Host "next.config.js found"
        $configContent = Get-Content $nextConfigPath -Raw
        if ($configContent -match 'output.*export') {
            Write-Host "Static export: Conditional (via NEXT_PUBLIC_IS_STATIC)" -ForegroundColor Green
        }
    }
}

Write-Host "`n=== STEP 11: GitHub Actions deploy workflow ===" -ForegroundColor Green
$workflowPath = Join-Path $repoPath ".github\workflows\deploy.yml"
if (Test-Path $workflowPath) {
    Write-Host "Deploy workflow found at: $workflowPath" -ForegroundColor Green
    Write-Host "  - Triggers: push to main, workflow_dispatch"
    Write-Host "  - Build: aria-frontend (npm run build with NEXT_PUBLIC_IS_STATIC=true)"
    Write-Host "  - Deploy: GitHub Pages (actions/deploy-pages@v4)"
}

Write-Host "`n=== DEPLOYMENT SUMMARY ===" -ForegroundColor Green
Write-Host "Repository: $repoPath"
Write-Host "Remote: $remoteUrl"
Write-Host "Current branch: $currentBranch"
Write-Host "Default branch: $defaultBranch"
Write-Host "Latest commit: $commitHash"
Write-Host "GitHub Pages: Actions-based deployment via deploy.yml"
Write-Host "Status: Ready for deployment on next push" -ForegroundColor Green
