# PowerShell equivalent of Makefile for ESGIS Chatbot

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [ValidateSet('bot', 'clean', 'venv', 'install', 'build', 'deploy-local', 'deploy', 'serve', 'test', 'test-endpoint', 'help')]
    [string]$target = "help",
    
    [Parameter()]
    [string]$env = "dev",
    
    [Parameter()]
    [string]$AWS_REGION = "eu-west-3",
    
    [Parameter()]
    [string]$AWS_PROFILE = "esgis_profile"
)

# Set environment variables
$env:AWS_REGION = $AWS_REGION
$env:AWS_PROFILE = $AWS_PROFILE

# Project Directories
$VENV_DIR = "$PSScriptRoot\venv"
$SRC_DIR = "$PSScriptRoot\src"

function Show-Help {
    Write-Host "ESGIS Chatbot Build System" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    Write-Host "Available targets:" -ForegroundColor Yellow
    Write-Host "  .\make.ps1 bot            - Run the Telegram bot"
    Write-Host "  .\make.ps1 clean          - Clean build artifacts"
    Write-Host "  .\make.ps1 venv           - Create virtual environment"
    Write-Host "  .\make.ps1 install        - Install dependencies"
    Write-Host "  .\make.ps1 build          - Build with SAM"
    Write-Host "  .\make.ps1 deploy-local   - Start local API"
    Write-Host "  .\make.ps1 deploy         - Deploy to AWS"
    Write-Host "  .\make.ps1 serve           - Run FastAPI development server"
    Write-Host "  .\make.ps1 test            - Run tests"
    Write-Host "  .\make.ps1 test-endpoint   - Test API endpoint"
    Write-Host "  .\make.ps1 webhook-status  - Show webhook status"
    Write-Host "  .\make.ps1 webhook-delete  - Delete existing webhook"
    Write-Host "  .\make.ps1 webhook-setup   - Setup webhook (use -webhook_url to specify URL)"
    Write-Host "  .\make.ps1 help            - Show this help"
    Write-Host ""
    Write-Host "Environment variables:" -ForegroundColor Yellow
    Write-Host "  env           - Environment name (default: dev)"
    Write-Host "  AWS_REGION    - AWS region (default: eu-west-3)"
    Write-Host "  AWS_PROFILE   - AWS profile (default: esgis_profile)"
    Write-Host "  webhook_url   - Webhook URL (for webhook-setup command)"
}

function Invoke-Bot {
    Write-Host "Starting Telegram bot..." -ForegroundColor Green
    python -m src.telegram_bot
}

function Invoke-Clean {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Green
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $VENV_DIR
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$PSScriptRoot\__pycache__"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$PSScriptRoot\*.egg-info"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$PSScriptRoot\.pytest_cache"
    Write-Host "Clean complete." -ForegroundColor Green
}

function New-VirtualEnvironment {
    param(
        [switch]$Force = $false
    )
    
    if ($Force) {
        Invoke-Clean
    }
    
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv $VENV_DIR
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
    
    Write-Host "Virtual environment created at $VENV_DIR" -ForegroundColor Green
}

function Install-Dependencies {
    if (-not (Test-Path $VENV_DIR)) {
        Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
        New-VirtualEnvironment
    }
    
    Write-Host "Installing dependencies..." -ForegroundColor Green
    & "$VENV_DIR\Scripts\pip" install -r "$PSScriptRoot\requirements-lambda.txt"
    & "$VENV_DIR\Scripts\pip" install -r "$PSScriptRoot\requirements.txt"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
    
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
}

function Invoke-Build {
    Write-Host "Building with SAM..." -ForegroundColor Green
    sam build --use-container -t infrastructure/template.yaml
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
}

function Start-LocalApi {
    Write-Host "Starting local API..." -ForegroundColor Green
    sam local start-api
}

function Invoke-Deploy {
    Write-Host "Deploying to $env environment..." -ForegroundColor Green
    
    # Optimize Lambda package
    Write-Host "Optimizing Lambda package..." -ForegroundColor Cyan
    Copy-Item -Path "$PSScriptRoot\requirements-lambda.txt" -Destination "$PSScriptRoot\requirements.txt" -Force
    
    # Ensure mangum is installed
    Write-Host "Installing mangum in virtual environment..." -ForegroundColor Cyan
    & "$VENV_DIR\Scripts\pip" install mangum
    
    # Build with SAM
    Write-Host "Building with SAM..." -ForegroundColor Cyan
    sam build --use-container --template-file infrastructure/template.yaml --parameter-overrides "EnvironmentName=$env"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
    
    # Verify mangum is in the package
    Write-Host "Checking if mangum is in the package..." -ForegroundColor Cyan
    Get-ChildItem -Path ".aws-sam\build\Function" -Recurse | Select-Object -First 10 | Format-Table Name
    
    # Install dependencies in the package
    Write-Host "Installing dependencies in the package..." -ForegroundColor Cyan
    & "$VENV_DIR\Scripts\pip" install -r "$PSScriptRoot\requirements.txt" -t ".aws-sam\build\Function"
    
    # Deploy with SAM
    Write-Host "Deploying with SAM..." -ForegroundColor Cyan
    $stackName = "multi-stack-$env"
    
    sam deploy --resolve-s3 --stack-name $stackName `
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --region $AWS_REGION `
        --parameter-overrides "EnvironmentName=$env TelegramBotToken=$env:TELEGRAM_BOT_TOKEN MistralApiKey=$env:MISTRAL_API_KEY" `
        --no-fail-on-empty-changeset
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Deployment failed"
        exit 1
    }
    
    Write-Host "Deployment completed successfully" -ForegroundColor Green
}

function Start-Server {
    Write-Host "Starting FastAPI development server..." -ForegroundColor Green
    & "$VENV_DIR\Scripts\uvicorn" src.main:app --reload
}

function Invoke-Tests {
    Write-Host "Running tests..." -ForegroundColor Green
    # & "$VENV_DIR\Scripts\pytest"
    Write-Host "Test command is currently commented out in the Makefile" -ForegroundColor Yellow
}

function Test-Endpoint {
    Write-Host "Testing API endpoint for environment: $env" -ForegroundColor Green
    
    $stackName = "multi-stack-$env"
    $apiUrl = aws cloudformation describe-stacks --stack-name $stackName --region $AWS_REGION `
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
    
    if (-not $apiUrl) {
        Write-Error "Failed to get API URL from CloudFormation stack"
        exit 1
    }
    
    Write-Host "Testing endpoint: $apiUrl" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $apiUrl -Method Get -UseBasicParsing
        Write-Host "Response status code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response body: $($response.Content)" -ForegroundColor Cyan
    } catch {
        Write-Error "Failed to call endpoint: $_"
    }
}

function Invoke-WebhookStatus {
    Write-Host "Checking webhook status..." -ForegroundColor Green
    python -m src.utils.webhook_cli status
}

function Invoke-WebhookDelete {
    Write-Host "Deleting webhook..." -ForegroundColor Green
    python -m src.utils.webhook_cli delete --force
}

function Invoke-WebhookSetup {
    param (
        [string]$url = $null
    )
    
    if (-not $url) {
        $url = Read-Host "Enter webhook base URL (e.g., https://your-api-url.com)"
    }
    
    if (-not $url) {
        Write-Host "Error: Webhook URL is required" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Setting up webhook to $url..." -ForegroundColor Green
    python -m src.utils.webhook_cli setup --url $url
}

# Main script execution
switch ($target.ToLower()) {
    "bot"            { Invoke-Bot }
    "clean"          { Invoke-Clean }
    "venv"           { New-VirtualEnvironment -Force }
    "install"        { Install-Dependencies }
    "build"          { Invoke-Build }
    "deploy-local"   { Start-LocalApi }
    "deploy"         { Invoke-Deploy }
    "serve"          { Start-Server }
    "test"           { Invoke-Tests }
    "test-endpoint"  { Test-Endpoint }
    "webhook-status" { Invoke-WebhookStatus }
    "webhook-delete" { Invoke-WebhookDelete }
    "webhook-setup"  { Invoke-WebhookSetup -url $webhook_url }
    "help"           { Show-Help }
    default          { Write-Host "Unknown target: $target" -ForegroundColor Red; Show-Help }
}
