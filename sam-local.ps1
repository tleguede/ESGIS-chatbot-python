# Script PowerShell pour faciliter le développement avec AWS SAM
param (
    [string]$Command = "help",
    [string]$Stage = "dev"
)

# Définir les couleurs pour une meilleure lisibilité
$colorSuccess = "Green"
$colorInfo = "Cyan" 
$colorWarning = "Yellow"
$colorError = "Red"

function Show-Help {
    Write-Host "Script d'aide pour AWS SAM Local" -ForegroundColor $colorInfo
    Write-Host "=================================" -ForegroundColor $colorInfo
    Write-Host ""
    Write-Host "Commandes disponibles:" -ForegroundColor $colorInfo
    Write-Host "  help       : Affiche cette aide" -ForegroundColor $colorInfo
    Write-Host "  start      : Démarre l'environnement Docker simulant AWS Lambda" -ForegroundColor $colorInfo
    Write-Host "  stop       : Arrête l'environnement Docker" -ForegroundColor $colorInfo
    Write-Host "  logs       : Affiche les logs de l'application" -ForegroundColor $colorInfo
    Write-Host "  local-api  : Démarre l'API localement avec sam local start-api" -ForegroundColor $colorInfo
    Write-Host "  validate   : Valide le template SAM" -ForegroundColor $colorInfo
    Write-Host "  build      : Construit l'application pour le déploiement" -ForegroundColor $colorInfo
    Write-Host "  deploy     : Déploie l'application sur AWS (nécessite AWS CLI configuré)" -ForegroundColor $colorInfo
    Write-Host ""
    Write-Host "Exemples:" -ForegroundColor $colorInfo
    Write-Host "  .\sam-local.ps1 start" -ForegroundColor $colorInfo
    Write-Host "  .\sam-local.ps1 deploy -Stage prod" -ForegroundColor $colorInfo
}

function Start-DockerEnvironment {
    Write-Host "Démarrage de l'environnement Docker simulant AWS Lambda..." -ForegroundColor $colorInfo
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Environnement Docker démarré avec succès!" -ForegroundColor $colorSuccess
        Write-Host "📋 Accédez à l'API à l'adresse: http://localhost:3000" -ForegroundColor $colorSuccess
    } else {
        Write-Host "❌ Erreur lors du démarrage de l'environnement Docker" -ForegroundColor $colorError
    }
}

function Stop-DockerEnvironment {
    Write-Host "Arrêt de l'environnement Docker..." -ForegroundColor $colorInfo
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Environnement Docker arrêté avec succès!" -ForegroundColor $colorSuccess
    } else {
        Write-Host "❌ Erreur lors de l'arrêt de l'environnement Docker" -ForegroundColor $colorError
    }
}

function Show-Logs {
    Write-Host "Affichage des logs de l'application..." -ForegroundColor $colorInfo
    docker-compose logs -f
}

function Start-LocalApi {
    Write-Host "Démarrage de l'API localement avec SAM..." -ForegroundColor $colorInfo
    sam local start-api --port 3000
}

function Validate-Template {
    Write-Host "Validation du template SAM..." -ForegroundColor $colorInfo
    sam validate
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Template SAM valide!" -ForegroundColor $colorSuccess
    } else {
        Write-Host "❌ Erreur dans le template SAM" -ForegroundColor $colorError
    }
}

function Build-Application {
    Write-Host "Construction de l'application pour le déploiement..." -ForegroundColor $colorInfo
    sam build
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Application construite avec succès!" -ForegroundColor $colorSuccess
    } else {
        Write-Host "❌ Erreur lors de la construction de l'application" -ForegroundColor $colorError
    }
}

function Deploy-Application {
    Write-Host "Déploiement de l'application sur AWS (Stage: $Stage)..." -ForegroundColor $colorInfo
    
    # Vérifier si AWS CLI est configuré
    try {
        $awsIdentity = aws sts get-caller-identity | ConvertFrom-Json
        Write-Host "Déploiement avec le compte AWS: $($awsIdentity.Account)" -ForegroundColor $colorInfo
    } catch {
        Write-Host "❌ AWS CLI n'est pas configuré correctement. Exécutez 'aws configure' d'abord." -ForegroundColor $colorError
        return
    }
    
    # Construire l'application si ce n'est pas déjà fait
    if (-not (Test-Path -Path ".aws-sam")) {
        Write-Host "Construction de l'application avant le déploiement..." -ForegroundColor $colorInfo
        sam build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erreur lors de la construction de l'application" -ForegroundColor $colorError
            return
        }
    }
    
    # Déployer avec le bon stage
    sam deploy --stack-name "esgis-chatbot-$Stage" --parameter-overrides "Stage=$Stage" --no-confirm-changeset
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Application déployée avec succès!" -ForegroundColor $colorSuccess
        
        # Afficher les outputs du stack
        Write-Host "Informations sur le déploiement:" -ForegroundColor $colorInfo
        aws cloudformation describe-stacks --stack-name "esgis-chatbot-$Stage" --query "Stacks[0].Outputs" --output table
    } else {
        Write-Host "❌ Erreur lors du déploiement de l'application" -ForegroundColor $colorError
    }
}

# Exécuter la commande demandée
switch ($Command) {
    "help" { Show-Help }
    "start" { Start-DockerEnvironment }
    "stop" { Stop-DockerEnvironment }
    "logs" { Show-Logs }
    "local-api" { Start-LocalApi }
    "validate" { Validate-Template }
    "build" { Build-Application }
    "deploy" { Deploy-Application }
    default {
        Write-Host "❌ Commande inconnue: $Command" -ForegroundColor $colorError
        Show-Help
    }
}
