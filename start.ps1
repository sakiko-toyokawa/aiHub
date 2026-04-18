# AI Knowledge Hub - Quick Start Script (PowerShell)
# One-click start without Docker

param(
    [switch]$SkipInstall,      # Skip dependency installation
    [switch]$SkipFrontend,     # Backend only
    [switch]$SkipBackend,      # Frontend only
    [switch]$Help              # Show help
)

if ($Help) {
    Write-Host @"
Usage: .\start.ps1 [options]

Options:
  -SkipInstall      Skip dependency installation
  -SkipFrontend     Start backend service only
  -SkipBackend      Start frontend service only
  -Help             Show this help message

Examples:
  .\start.ps1                    # Full start
  .\start.ps1 -SkipInstall       # Skip installation, start directly
  .\start.ps1 -SkipFrontend      # Backend only
"@ -ForegroundColor Cyan
    exit
}

# Set console encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Color definitions
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

function Write-Banner {
    $banner = @"
============================================================
         AI Knowledge Hub - Quick Start Script

  Auto-crawl AI knowledge | Daily email digest | Elegant UI
============================================================
"@
    Write-Host $banner -ForegroundColor $Cyan
}

function Write-Step($message) {
    Write-Host "`n[>] $message" -ForegroundColor $Cyan
}

function Write-Success($message) {
    Write-Host "[OK] $message" -ForegroundColor $Green
}

function Write-Warning($message) {
    Write-Host "[WARN] $message" -ForegroundColor $Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor $Red
}

Write-Banner

# Get project paths
$PROJECT_DIR = $PSScriptRoot
$BACKEND_DIR = Join-Path $PROJECT_DIR "backend"
$FRONTEND_DIR = Join-Path $PROJECT_DIR "frontend"
$VENV_DIR = Join-Path $BACKEND_DIR ".venv"

Write-Host "Project Directory: $PROJECT_DIR" -ForegroundColor $Yellow
Write-Host ""

# Check Python
Write-Step "Checking Python environment..."
$pythonVersion = python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python not found. Please install Python 3.10+"
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor $Yellow
    exit 1
}
Write-Success "Python $pythonVersion"

# Check Node.js
Write-Step "Checking Node.js environment..."
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Node.js not found. Please install Node.js 18+"
    Write-Host "Download: https://nodejs.org/" -ForegroundColor $Yellow
    exit 1
}
Write-Success "Node.js $nodeVersion"
Write-Host ""

# Check .env file
Write-Step "Checking environment configuration..."
$envFile = Join-Path $BACKEND_DIR ".env"
$envExample = Join-Path $BACKEND_DIR ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Warning "Created default .env file"
        Write-Host "   Please edit $envFile to configure your API keys" -ForegroundColor $Yellow
    } else {
        Write-Warning ".env file not found, will use default configuration"
    }
} else {
    Write-Success "Environment configuration file exists"
}
Write-Host ""

# Create virtual environment
if (-not $SkipInstall) {
    Write-Step "Setting up Python virtual environment..."
    if (-not (Test-Path $VENV_DIR)) {
        Write-Host "   Creating virtual environment..." -NoNewline
        python -m venv $VENV_DIR
        if ($LASTEXITCODE -ne 0) {
            Write-Host " FAILED" -ForegroundColor $Red
            exit 1
        }
        Write-Host " OK" -ForegroundColor $Green
    } else {
        Write-Success "Virtual environment already exists"
    }
    Write-Host ""

    # Install backend dependencies
    Write-Step "Installing backend dependencies..."
    $activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
    & $activateScript

    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
    pip install --only-binary :all: -i https://pypi.tuna.tsinghua.edu.cn/simple -r (Join-Path $BACKEND_DIR "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install backend dependencies"
        exit 1
    }
    Write-Success "Backend dependencies installed"
    Write-Host ""
}

# Install frontend dependencies
if (-not $SkipInstall -and -not $SkipFrontend) {
    Write-Step "Installing frontend dependencies..."
    Set-Location $FRONTEND_DIR

    if (-not (Test-Path "node_modules")) {
        npm install | Out-String | Write-Verbose
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install frontend dependencies"
            exit 1
        }
        Write-Success "Frontend dependencies installed"
    } else {
        Write-Success "Frontend dependencies already exist"
    }
    Write-Host ""
}

Set-Location $PROJECT_DIR

# Start backend
if (-not $SkipBackend) {
    Write-Step "Starting backend service..."
    $backendScript = {
        param($dir, $venv)
        Set-Location $dir
        & "$venv\Scripts\Activate.ps1"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }

    Start-Process powershell -ArgumentList "-Command", "& {$backendScript} -dir '$BACKEND_DIR' -venv '$VENV_DIR'" -WindowStyle Normal

    Write-Success "Backend started"
    Write-Host "   URL:  http://localhost:8000" -ForegroundColor $Yellow
    Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor $Yellow
    Write-Host ""

    # Wait for backend to be ready
    Write-Host "Waiting for backend to be ready..." -NoNewline
    $retries = 0
    $maxRetries = 30
    $ready = $false

    while ($retries -lt $maxRetries -and -not $ready) {
        Start-Sleep -Milliseconds 500
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $ready = $true
            }
        } catch {
            $retries++
        }
    }

    if ($ready) {
        Write-Host " OK" -ForegroundColor $Green
    } else {
        Write-Host " (may need more time)" -ForegroundColor $Yellow
    }
    Write-Host ""
}

# Start frontend
if (-not $SkipFrontend) {
    Write-Step "Starting frontend service..."
    $frontendScript = {
        param($dir)
        Set-Location $dir
        npm run dev
    }

    Start-Process powershell -ArgumentList "-Command", "& {$frontendScript} -dir '$FRONTEND_DIR'" -WindowStyle Normal

    Write-Success "Frontend started"
    Write-Host "   URL: http://localhost:5173" -ForegroundColor $Yellow
    Write-Host ""
}

# Print final info
$info = @"
============================================================
[OK] All services started!

Access URLs:
   Frontend:    http://localhost:5173
   Backend API: http://localhost:8000
   API Docs:    http://localhost:8000/docs

Useful commands:
   Test email: cd backend && python -c "import asyncio; from notifier.email_sender import send_daily_digest; asyncio.run(send_daily_digest())"
   View logs:  Check the opened command line windows
   Stop:       Close the corresponding command line windows

Tip: First time use? Please configure API keys in .env file
============================================================
"@
Write-Host $info -ForegroundColor $Cyan

# Keep window open
Write-Host "Press Enter to close this window..." -ForegroundColor $Yellow
$null = Read-Host
