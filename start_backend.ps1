# Start the FastAPI backend server
Write-Host "Starting Nyaya-Sahayak Backend..." -ForegroundColor Green

# Navigate to backend directory
Set-Location -Path "$PSScriptRoot\backend"

# Activate virtual environment if it exists
if (Test-Path "..\venv\Scripts\Activate.ps1") {
    & "..\venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Cyan
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start the server
Write-Host "`nStarting server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

uvicorn main:app --reload --host 0.0.0.0 --port 8000
