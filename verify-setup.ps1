# Verify Setup for Real Calling Integration
Write-Host "🔍 Verifying AI Doctor Appointment Setup" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check directories
Write-Host "📁 Checking directories..." -ForegroundColor Yellow
$dirs = @("frontend", "app-backend", "gemini-twillio-calling")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "  ✅ $dir/" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $dir/ NOT FOUND" -ForegroundColor Red
        $allGood = $false
    }
}

Write-Host ""
Write-Host "🔑 Checking unified .env file..." -ForegroundColor Yellow

# Check root .env (unified config)
if (Test-Path ".env") {
    Write-Host "  ✅ .env exists in root directory" -ForegroundColor Green
    $envContent = Get-Content ".env" -Raw
    
    # Check Google Places API
    if ($envContent -match 'REACT_APP_GOOGLE_PLACES_API_KEY=.+') {
        Write-Host "     ✅ Google Places API key set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Google Places API key missing" -ForegroundColor Yellow
        $allGood = $false
    }
    
    # Check Backend URL
    if ($envContent -match 'REACT_APP_BACKEND_URL=.+') {
        Write-Host "     ✅ Backend URL set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Backend URL missing" -ForegroundColor Yellow
    }
    
    # Check Test Phone Number
    if ($envContent -match 'REACT_APP_TEST_PHONE_NUMBER=\+\d+') {
        Write-Host "     ✅ Test phone number set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Test phone number missing/invalid" -ForegroundColor Yellow
    }
    
    # Check Twilio credentials
    if ($envContent -match 'TWILIO_ACCOUNT_SID=AC.+') {
        Write-Host "     ✅ Twilio Account SID set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Twilio Account SID missing" -ForegroundColor Yellow
    }
    
    if ($envContent -match 'TWILIO_AUTH_TOKEN=.+') {
        Write-Host "     ✅ Twilio Auth Token set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Twilio Auth Token missing" -ForegroundColor Yellow
    }
    
    if ($envContent -match 'TWILIO_PHONE_NUMBER=\+.+') {
        Write-Host "     ✅ Twilio Phone Number set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Twilio Phone Number missing" -ForegroundColor Yellow
    }
    
    # Check Google API Key for Gemini
    if ($envContent -match 'GOOGLE_API_KEY=.+') {
        Write-Host "     ✅ Google Gemini API key set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Google Gemini API key missing" -ForegroundColor Yellow
    }
    
    # Check NGROK URL
    if ($envContent -match 'NGROK_URL=https://.+') {
        Write-Host "     ✅ NGROK URL set" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  NGROK URL missing (required for calling)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ .env NOT FOUND in root directory" -ForegroundColor Red
    Write-Host "     This is the unified config file for all services" -ForegroundColor Gray
    Write-Host "     See .env example structure in the file" -ForegroundColor Gray
    $allGood = $false
}

Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow

# Check frontend node_modules
if (Test-Path "frontend\node_modules") {
    Write-Host "  ✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ❌ Frontend dependencies NOT installed" -ForegroundColor Red
    Write-Host "     Run: cd frontend; npm install" -ForegroundColor Gray
    $allGood = $false
}

# Check app-backend venv
if (Test-Path "app-backend\venv") {
    Write-Host "  ✅ Backend virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Backend virtual environment NOT found" -ForegroundColor Yellow
    Write-Host "     Run: cd app-backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Gray
}

# Check gemini-twillio-calling venv
if (Test-Path "gemini-twillio-calling\.venv") {
    Write-Host "  ✅ Gemini-Twilio virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Gemini-Twilio virtual environment NOT found" -ForegroundColor Yellow
    Write-Host "     See gemini-twillio-calling/README.md for setup" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🌐 Checking ngrok..." -ForegroundColor Yellow
try {
    $ngrokResponse = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2 -ErrorAction Stop
    $ngrokData = $ngrokResponse.Content | ConvertFrom-Json
    if ($ngrokData.tunnels.Count -gt 0) {
        $httpsUrl = ($ngrokData.tunnels | Where-Object { $_.proto -eq "https" }).public_url
        Write-Host "  ✅ ngrok is running" -ForegroundColor Green
        Write-Host "     URL: $httpsUrl" -ForegroundColor Cyan
        Write-Host "     ⚠️  Make sure this URL is in your .env files!" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚠️  ngrok running but no tunnels found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ ngrok NOT running" -ForegroundColor Red
    Write-Host "     Run: ngrok http 8000" -ForegroundColor Gray
    Write-Host "     Then update NGROK_URL in .env files" -ForegroundColor Gray
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if ($allGood) {
    Write-Host "✅ Setup looks good! You're ready to start." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Make sure ngrok is running: ngrok http 8000" -ForegroundColor White
    Write-Host "  2. Update NGROK_URL in .env file" -ForegroundColor White
    Write-Host "  3. (Optional) Run: .\sync-env.ps1 to copy to all folders" -ForegroundColor White
    Write-Host "  4. Run: .\start-all.ps1" -ForegroundColor White
} else {
    Write-Host "⚠️  Some issues found. Please fix them before starting." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick setup:" -ForegroundColor Cyan
    Write-Host "  1. Edit .env in root directory (all config in one place!)" -ForegroundColor White
    Write-Host "  2. Run: cd frontend; npm install" -ForegroundColor White
    Write-Host "  3. Run: cd app-backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor White
    Write-Host "  4. Services auto-load from root .env" -ForegroundColor White
}

Write-Host ""
Write-Host "💡 All configuration is now in ONE file: .env (root)" -ForegroundColor Cyan
