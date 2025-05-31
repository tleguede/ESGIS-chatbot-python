# ESGIS Chatbot Python

Un chatbot Telegram intégré avec Mistral AI, développé en Python.

## Description

Ce projet est une version Python du chatbot Telegram qui utilise l'API Mistral AI pour générer des réponses intelligentes. Il est conçu pour être déployé sur AWS Lambda, mais peut également fonctionner comme une application autonome.

## Fonctionnalités

- Bot Telegram interactif
- Intégration avec Mistral AI pour la génération de réponses
- API REST pour interagir avec le chatbot
- Stockage des conversations (mémoire, DynamoDB)
- Documentation API avec Swagger
- Support pour le déploiement AWS Lambda
- Multilingue (français, anglais, espagnol)
- Système de feedback utilisateur

## Prérequis

- Python 3.9+
- Un token de bot Telegram (obtenu via [@BotFather](https://t.me/BotFather))
- Une clé API Mistral AI

## Installation

1. Cloner le dépôt
2. Installer les dépendances:
   ```
   pip install -r requirements.txt
   ```
3. Copier `.env.example` vers `.env` et configurer les variables d'environnement

## Démarrage rapide

Pour démarrer le bot en mode développement:

```bash
python -m src.main
```

## Déploiement

### Déploiement local

Pour tester l'application localement:

```bash
uvicorn src.main:app --reload
```

## Utilisation avec GitHub Codespaces

Ce projet est configuré pour fonctionner avec GitHub Codespaces, ce qui vous permet de développer et tester l'application dans un environnement cloud sans installation locale.

### Démarrer avec Codespaces

1. Sur GitHub, naviguez vers le dépôt du projet
2. Cliquez sur le bouton vert "Code"
3. Sélectionnez l'onglet "Codespaces"
4. Cliquez sur "Create codespace on main"

### Fonctionnalités disponibles dans Codespaces

- Environnement de développement préconfiguré avec toutes les dépendances
- Simulation d'AWS Lambda pour tester le déploiement serverless
- DynamoDB local pour les tests de persistance
- Extensions VS Code préinstallées pour le développement Python et AWS

### Commandes utiles dans Codespaces

```bash
# Démarrer l'application en mode développement
python -m src.app

# Tester l'API avec SAM local
sam local start-api --port 3000

# Construire l'application pour déploiement
sam build

# Déployer sur AWS (nécessite configuration AWS)
sam deploy --guided
```

### Variables d'environnement

Dans Codespaces, vous devez configurer vos variables d'environnement dans les secrets du dépôt GitHub ou les ajouter manuellement au fichier `.env` après le démarrage de votre espace de code.

### Déploiement AWS

Pour déployer sur AWS Lambda:

```bash
sam deploy --guided --template-file infrastructure/template.yaml
```

## Structure du projet

```
esgis-chatbot-python/
├── infrastructure/        # Templates CloudFormation
├── src/                   # Code source
│   ├── config/            # Configuration
│   ├── controllers/       # Contrôleurs API
│   ├── db/                # Adaptateurs de base de données
│   │   └── adapters/      # Implémentations spécifiques
│   ├── routes/            # Routes API
│   ├── services/          # Services métier
│   ├── app.py             # Application FastAPI
│   ├── lambda.py          # Point d'entrée AWS Lambda
│   └── main.py            # Point d'entrée principal
├── .env.example           # Exemple de configuration
├── Jenkinsfile            # Configuration CI/CD
└── requirements.txt       # Dépendances Python
```

## Commandes du bot

- `/start` - Démarrer la conversation et afficher le menu
- `/chat` - Commencer à discuter avec l'IA
- `/reset` - Réinitialiser l'historique de conversation
- `/help` - Afficher les commandes disponibles

## Licence

Ce projet est sous licence MIT.
