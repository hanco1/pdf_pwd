# Script to push files to GitHub
# This script will try to find git and push your files

$ErrorActionPreference = "Stop"

# Common git installation paths
$gitPaths = @(
    "git",
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe",
    "$env:ProgramFiles\Git\cmd\git.exe"
)

$gitCmd = $null
foreach ($path in $gitPaths) {
    try {
        if ($path -eq "git") {
            $result = Get-Command git -ErrorAction SilentlyContinue
            if ($result) {
                $gitCmd = "git"
                break
            }
        } else {
            if (Test-Path $path) {
                $gitCmd = $path
                break
            }
        }
    } catch {
        continue
    }
}

if (-not $gitCmd) {
    Write-Host "Git not found. Please install Git from https://git-scm.com/download/win" -ForegroundColor Red
    Write-Host "Or add Git to your PATH environment variable." -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Git: $gitCmd" -ForegroundColor Green

# Change to project directory
$projectDir = "D:\PDF unlock"
Set-Location $projectDir

# Check git status
Write-Host "`nChecking git status..." -ForegroundColor Cyan
& $gitCmd status

# Add all files
Write-Host "`nAdding files..." -ForegroundColor Cyan
& $gitCmd add .

# Check if there are changes to commit
$status = & $gitCmd status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "`nNo changes to commit." -ForegroundColor Yellow
    exit 0
}

# Commit
Write-Host "`nCommitting changes..." -ForegroundColor Cyan
$commitMessage = "Update PDF unlocker files"
& $gitCmd commit -m $commitMessage

# Push to GitHub
Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
& $gitCmd push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccessfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "`nPush failed. You may need to set up authentication." -ForegroundColor Red
    Write-Host "If this is your first push, you might need to run:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor Yellow
}

