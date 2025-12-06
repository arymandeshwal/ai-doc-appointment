# Sync root .env to all service directories
# This ensures all services can access the unified configuration

Write-Host "🔄 Syncing .env file to all services..." -ForegroundColor Cyan
Write-Host ""

$rootEnv = ".\\.env"

if (-not (Test-Path $rootEnv)) {
    Write-Host "❌ Error: .env file not found in root directory" -ForegroundColor Red
    Write-Host "   Please create .env in the root with all configuration" -ForegroundColor Yellow
    exit 1
}

Write-Host "📄 Source: .env (root)" -ForegroundColor Green

# Frontend
if (Test-Path ".\\frontend") {
    Copy-Item $rootEnv ".\\frontend\\.env" -Force
    Write-Host "  ✅ Copied to frontend/.env" -ForegroundColor Green
}

# App Backend
if (Test-Path ".\\app-backend") {
    Copy-Item $rootEnv ".\\app-backend\\.env" -Force
    Write-Host "  ✅ Copied to app-backend/.env" -ForegroundColor Green
}

# Gemini-Twilio
if (Test-Path ".\\gemini-twillio-calling") {
    Copy-Item $rootEnv ".\\gemini-twillio-calling\\.env" -Force
    Write-Host "  ✅ Copied to gemini-twillio-calling/.env" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ All .env files synced successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Note: Services now automatically load from root .env" -ForegroundColor Yellow
Write-Host "   You can edit the root .env file and restart services" -ForegroundColor Yellow
