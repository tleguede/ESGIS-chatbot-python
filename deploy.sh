#!/bin/bash

# Script de déploiement pour le chatbot Telegram sur AWS Lambda

# Variables
STACK_NAME="chatbot-stack"
ENVIRONMENT="dev"  # Par défaut, on utilise l'environnement de développement
REGION="eu-west-3"  # Paris
BUCKET_NAME="chatbot-deployment-bucket-$(date +%s)"

# Vérifier que les outils nécessaires sont installés
command -v aws >/dev/null 2>&1 || { echo >&2 "AWS CLI requis mais non installé. Abandon..."; exit 1; }
command -v sam >/dev/null 2>&1 || { echo >&2 "AWS SAM CLI requis mais non installé. Abandon..."; exit 1; }

# Demander les informations de configuration
read -p "Nom de la pile CloudFormation [$STACK_NAME]: " input
STACK_NAME=${input:-$STACK_NAME}

read -p "Environnement (dev/preprod/prod) [$ENVIRONMENT]: " input
ENVIRONMENT=${input:-$ENVIRONMENT}

read -p "Région AWS [$REGION]: " input
REGION=${input:-$REGION}

# Demander les variables sensibles
read -s -p "Token du bot Telegram: " TELEGRAM_BOT_TOKEN
echo ""

read -s -p "Clé API Mistral AI: " MISTRAL_API_KEY
echo ""

# Créer un bucket S3 pour les artefacts de déploiement
BUCKET_NAME="${BUCKET_NAME}-${ENVIRONMENT}"
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
    echo "Création du bucket S3 $BUCKET_NAME..."
    aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
else
    echo "Le bucket S3 $BUCKET_NAME existe déjà."
fi

# Construire l'application SAM
echo "Construction de l'application SAM..."
sam build \
    --template-file infrastructure/template.yaml \
    --build-dir .aws-sam/build \
    --use-container \
    --cached

# Empaqueter l'application pour le déploiement
echo "Empaquetage de l'application..."
sam package \
    --template-file .aws-sam/build/template.yaml \
    --output-template-file .aws-sam/build/packaged.yaml \
    --s3-bucket "$BUCKET_NAME" \
    --region "$REGION"

# Déployer l'application
echo "Déploiement de l'application sur AWS..."
sam deploy \
    --template-file .aws-sam/build/packaged.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        EnvironmentName="$ENVIRONMENT" \
        TelegramBotToken="$TELEGRAM_BOT_TOKEN" \
        MistralApiKey="$MISTRAL_API_KEY" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --region "$REGION" \
    --no-fail-on-empty-changeset

# Récupérer les sorties de la pile
echo "Récupération des informations de sortie..."
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --region "$REGION" \
    --output table

echo "Déploiement terminé avec succès !"
echo "URL de l'API: $(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text --region "$REGION")"
