# Quick Start Script for Real Calling Demo
# Run this from the ai-doc-appointment root directory

Write-Host "🚀 Starting AI Doctor Appointment System with Real Calling" -ForegroundColor Cyan
Write-Host ""

# Check if running from correct directory
if (-not (Test-Path ".\frontend") -or -not (Test-Path ".\app-backend") -or -not (Test-Path ".\gemini-twillio-calling")) {
    Write-Host "❌ Error: Please run this script from the ai-doc-appointment root directory" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Pre-flight checklist:" -ForegroundColor Yellow
Write-Host "  1. ngrok is running (ngrok http 8000)" -ForegroundColor White
Write-Host "  2. .env files are configured in:" -ForegroundColor White
Write-Host "     - app-backend/.env" -ForegroundColor White
Write-Host "     - gemini-twillio-calling/.env" -ForegroundColor White
Write-Host "     - frontend/.env" -ForegroundColor White
Write-Host ""

$continue = Read-Host "Continue? (Y/N)"
if ($continue -ne "Y" -and $continue -ne "y") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🔧 Starting services..." -ForegroundColor Cyan

# Start Gemini-Twilio server (Terminal 1)
Write-Host "1️⃣  Starting Gemini-Twilio Voice Server (port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd gemini-twillio-calling; .\.venv\Scripts\Activate.ps1; python main.py"

Start-Sleep -Seconds 2

# Start Flask backend (Terminal 2)
Write-Host "2️⃣  Starting Flask Backend API (port 5000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd app-backend; .\venv\Scripts\Activate.ps1; python app.py"

Start-Sleep -Seconds 2

# Start React frontend (Terminal 3)
Write-Host "3️⃣  Starting React Frontend (port 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start"

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access the app at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Monitor services:" -ForegroundColor Yellow
Write-Host "  - Gemini-Twilio: http://localhost:8000" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:5000/api/health" -ForegroundColor White
Write-Host "  - ngrok Dashboard: http://127.0.0.1:4040" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Make sure ngrok is running: ngrok http 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window (services will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
