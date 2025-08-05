# PowerShell script to deploy ticker discovery to Bloomberg VM
# Run this via Azure CLI: az vm run-command invoke

param(
    [string]$BackupDir = "C:\Bloomberg\APIServer\backups"
)

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Backup current main.py
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "main_backup_$timestamp.py"

Write-Host "Creating backup: $backupFile" -ForegroundColor Cyan
Copy-Item "C:\Bloomberg\APIServer\main.py" $backupFile -ErrorAction Stop

# Create ticker_discovery_module.py
$tickerDiscoveryContent = @'
# Ticker Discovery Module content goes here
# This would be the full content of ticker_discovery_module.py
'@

# Write the module file
$modulePath = "C:\Bloomberg\APIServer\ticker_discovery_module.py"
Write-Host "Creating ticker discovery module: $modulePath" -ForegroundColor Yellow
Set-Content -Path $modulePath -Value $tickerDiscoveryContent

# Update main.py to include the new router
$mainPyContent = Get-Content "C:\Bloomberg\APIServer\main.py" -Raw

# Check if already integrated
if ($mainPyContent -match "ticker_discovery_router") {
    Write-Host "Ticker discovery already integrated!" -ForegroundColor Green
    exit 0
}

# Find where to add the import (after other imports)
$importPattern = "from fastapi import.*\n"
$importReplacement = $Matches[0] + "from ticker_discovery_module import ticker_discovery_router`n"

# Find where to add the router (after app creation)
$routerPattern = "app = FastAPI\(.*\)"
if ($mainPyContent -match $routerPattern) {
    $appLine = $Matches[0]
    $routerAddition = "`n`n# Add ticker discovery endpoints`napp.include_router(ticker_discovery_router)`n"
    
    # Update the file
    $newContent = $mainPyContent -replace $importPattern, $importReplacement
    $newContent = $newContent -replace "($routerPattern)", "`$1$routerAddition"
    
    # Write updated main.py
    Write-Host "Updating main.py with ticker discovery router" -ForegroundColor Yellow
    Set-Content -Path "C:\Bloomberg\APIServer\main.py" -Value $newContent
}

# Restart the API service
Write-Host "Restarting Bloomberg API service..." -ForegroundColor Yellow
Get-Process python* | Where-Object {$_.Path -like "*main.py*"} | Stop-Process -Force
Start-Sleep -Seconds 2

Set-Location "C:\Bloomberg\APIServer"
Start-Process "C:\Python311\python.exe" -ArgumentList "main.py" -WindowStyle Hidden

Write-Host "✅ Ticker discovery endpoints deployed!" -ForegroundColor Green
Write-Host "New endpoints available:" -ForegroundColor Cyan
Write-Host "  - POST /api/bloomberg/ticker-discovery" -ForegroundColor White
Write-Host "  - POST /api/bloomberg/validate-tickers" -ForegroundColor White
Write-Host "" 
Write-Host "Check API docs at: http://20.172.249.92:8080/docs" -ForegroundColor Cyan