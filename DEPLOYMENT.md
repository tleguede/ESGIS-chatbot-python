# Guide de déploiement du Chatbot Telegram sur AWS Lambda

Ce document explique comment déployer le chatbot Telegram sur AWS Lambda en utilisant AWS SAM (Serverless Application Model).

## Prérequis

1. **Compte AWS** avec les permissions nécessaires
2. **AWS CLI** installé et configuré
3. **AWS SAM CLI** installé
4. **Python 3.9** ou supérieur
5. **Git** (recommandé pour le contrôle de version)

## Configuration initiale

1. **Cloner le dépôt**
   ```bash
   git clone <url-du-depot>
   cd esgis-chatbot-python
   ```

2. **Créer un environnement virtuel** (recommandé)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```env
# Configuration de base
ENV=dev  # ou 'prod' pour la production

# Configuration Telegram
TELEGRAM_BOT_TOKEN=votre_token_telegram

# Configuration Mistral AI
MISTRAL_API_KEY=votre_cle_mistral

# Configuration DynamoDB (optionnel)
DYNAMO_TABLE=chatbot-table-${ENV}
```

## Déploiement avec le script

1. **Rendre le script exécutable** (Linux/Mac)
   ```bash
   chmod +x deploy.sh
   ```

2. **Exécuter le script de déploiement**
   ```bash
   ./deploy.sh
   ```

3. **Suivre les instructions** pour fournir les informations requises
   - Nom de la pile CloudFormation
   - Environnement (dev/preprod/prod)
   - Région AWS
   - Token du bot Telegram
   - Clé API Mistral AI

## Déploiement manuel

Si vous préférez déployer manuellement :

```bash
# Construire l'application
sam build --template-file infrastructure/template.yaml

# Empaqueter l'application
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket votre-bucket-de-deploiement

# Déployer l'application
sam deploy \
    --template-file packaged.yaml \
    --stack-name chatbot-stack \
    --capabilities CAPABILITY_IAM \
    --region eu-west-3 \
    --parameter-overrides \
        EnvironmentName=dev \
        TelegramBotToken=votre_token \
        MistralApiKey=votre_cle
```

## Configuration du webhook Telegram

Après le déploiement, configurez le webhook de Telegram pour qu'il pointe vers votre API Gateway :

```bash
API_URL=$(aws cloudformation describe-stacks \
    --stack-name chatbot-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

curl -F "url=${API_URL}api/chat/update" \
     https://api.telegram.org/bot<votre_token_telegram>/setWebhook
```

## Surveillance et logs

Les logs de l'application sont disponibles dans CloudWatch :

1. **Logs Lambda** : `/aws/lambda/chatbot-lambda-<environnement>`
2. **Logs API Gateway** : `/aws/apigateway/<environnement>-chatbot`

## Mise à jour du déploiement

Pour mettre à jour votre application :

1. Apportez vos modifications au code
2. Exécutez à nouveau le script de déploiement :
   ```bash
   ./deploy.sh
   ```

## Suppression de l'application

Pour supprimer toutes les ressources créées :

```bash
aws cloudformation delete-stack --stack-name chatbot-stack --region eu-west-3
```

## Dépannage

### Erreurs courantes

1. **Permissions insuffisantes**
   - Vérifiez que l'utilisateur AWS a les permissions nécessaires
   - Vérifiez les politiques IAM associées

2. **Échec du déploiement**
   - Vérifiez les logs CloudFormation pour plus de détails
   - Assurez-vous que le nom de la pile est unique dans la région

3. **Problèmes de connexion à DynamoDB**
   - Vérifiez que la table DynamoDB existe et est accessible
   - Vérifiez les politiques IAM de la fonction Lambda

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur le dépôt GitHub.
