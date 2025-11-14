# Cross-platform virtual environment setup script for ABSolution (PowerShell)

Write-Host "Setting up ABSolution virtual environment..." -ForegroundColor Cyan

# Create virtual environment if it doesn't exist
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Determine the correct activation script path
$activateScript = $null
if (Test-Path "venv\Scripts\Activate.ps1") {
    $activateScript = "venv\Scripts\Activate.ps1"
    Write-Host "Using Windows PowerShell activation script: $activateScript" -ForegroundColor Green
} elseif (Test-Path "venv/bin/activate") {
    $activateScript = "venv/bin/activate"
    Write-Host "Using Unix/Linux/Mac activation script: $activateScript" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find activation script in venv\Scripts\ or venv/bin/" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& $activateScript

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Warning: requirements.txt not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Virtual environment setup complete!" -ForegroundColor Cyan
Write-Host "To activate the virtual environment manually, run:" -ForegroundColor Cyan
Write-Host "  & $activateScript" -ForegroundColor White
