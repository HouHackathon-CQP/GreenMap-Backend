# Script to update CHANGELOG.md automatically
# Usage: .\update_changelog.ps1 [version]
# Example: .\update_changelog.ps1 1.1.0

param(
    [string]$Version = ""
)

Write-Host "Updating CHANGELOG with git-cliff..." -ForegroundColor Cyan

if ($Version) {
    # Generate changelog for a specific version
    Write-Host "Generating changelog for version v$Version..." -ForegroundColor Yellow
    git-cliff --tag "v$Version" --output CHANGELOG.md
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "CHANGELOG.md updated successfully for version v$Version!" -ForegroundColor Green
        Write-Host "Don't forget to commit the changes:" -ForegroundColor Yellow
        Write-Host "   git add CHANGELOG.md" -ForegroundColor Gray
        Write-Host "   git commit -m 'chore: update changelog for v$Version'" -ForegroundColor Gray
        Write-Host "   git tag -a v$Version -m 'Release v$Version'" -ForegroundColor Gray
        Write-Host "   git push origin main --tags" -ForegroundColor Gray
    } else {
        Write-Host "Failed to generate changelog!" -ForegroundColor Red
        exit 1
    }
} else {
    # Generate changelog with full history
    Write-Host "Generating changelog with full history..." -ForegroundColor Yellow
    git-cliff --output CHANGELOG.md
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "CHANGELOG.md updated successfully!" -ForegroundColor Green
        Write-Host "Don't forget to commit the changes:" -ForegroundColor Yellow
        Write-Host "   git add CHANGELOG.md" -ForegroundColor Gray
        Write-Host "   git commit -m 'docs: update changelog'" -ForegroundColor Gray
    } else {
        Write-Host "Failed to generate changelog!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "View the updated CHANGELOG.md to see the changes." -ForegroundColor Cyan
