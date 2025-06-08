# Makefile.ps1 - PowerShell equivalent for Makefile commands
# Usage: .\Makefile.ps1 <command>

param(
    [Parameter(Position=0, Mandatory=$true)]
    [string]$Command
)

$env:AWS_REGION = $env:AWS_REGION -or 'eu-west-3'
$env:AWS_PROFILE = $env:AWS_PROFILE -or 'esgis_profile'

function bot {
    python -m src.telegram_bot
}

function run {
    python -m src.main
}

function clean {
    if (Test-Path "venv") { Remove-Item -Recurse -Force "venv" }
    if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force "*.egg-info" }
    if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }
    if (Test-Path ".aws-sam") { Remove-Item -Recurse -Force ".aws-sam" }
}

function venv {
    python -m venv venv
    if (!(Test-Path "venv")) { Write-Host "Environnement virtuel déjà créé ou impossible à créer" }
}

function install {
    if (Test-Path "venv/Scripts/Activate.ps1") {
        . venv/Scripts/Activate.ps1
        pip install -r requirements.txt
    } else {
        Write-Host "Virtualenv non trouvé. Lancez d'abord 'venv' !"
    }
}

function test {
    # python -m pytest
    Write-Host "(Tests à implémenter)"
}

function build {
    sam build --use-container -t infrastructure/template.yaml
}

function deploy-local {
    sam local start-api
}

function deploy {
    param(
        [string]$env,
        [string]$TELEGRAM_BOT_TOKEN,
        [string]$MISTRAL_API_KEY
    )
    if (!$TELEGRAM_BOT_TOKEN) { Write-Error "Erreur: TELEGRAM_BOT_TOKEN est requis"; exit 1 }
    if (!$MISTRAL_API_KEY) { Write-Error "Erreur: MISTRAL_API_KEY est requis"; exit 1 }
    sam deploy --resolve-s3 --template-file infrastructure/template.yaml --stack-name "multi-stack-$env" \
        --capabilities CAPABILITY_IAM --region $env:AWS_REGION \
        --parameter-overrides \
            EnvironmentName=$env \
            TelegramBotToken=$TELEGRAM_BOT_TOKEN \
            MistralApiKey=$MISTRAL_API_KEY \
        --no-fail-on-empty-changeset
}

function serve {
    if (Test-Path "venv/Scripts/Activate.ps1") {
        . venv/Scripts/Activate.ps1
        python -m uvicorn src.main:app --reload --port 3000
    } else {
        Write-Host "Virtualenv non trouvé. Lancez d'abord 'venv' !"
    }
}

function test-endpoint {
    param([string]$env)
    Write-Host "Running endpoint tests..."
    $apiUrl = aws cloudformation describe-stacks --stack-name "multi-stack-$env" --region $env:AWS_REGION `
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
    if ($apiUrl) { curl -Method Get $apiUrl }
}

switch ($Command) {
    'bot'           { bot }
    'run'           { run }
    'clean'         { clean }
    'venv'          { venv }
    'install'       { install }
    'test'          { test }
    'build'         { build }
    'deploy-local'  { deploy-local }
    'deploy'        { 
        $env = $env:env
        $TELEGRAM_BOT_TOKEN = $env:TELEGRAM_BOT_TOKEN
        $MISTRAL_API_KEY = $env:MISTRAL_API_KEY
        deploy -env $env -TELEGRAM_BOT_TOKEN $TELEGRAM_BOT_TOKEN -MISTRAL_API_KEY $MISTRAL_API_KEY
    }
    'serve'         { serve }
    'test-endpoint' {
        $env = $env:env
        test-endpoint -env $env
    }
    default         { Write-Host "Commande inconnue: $Command" }
}
