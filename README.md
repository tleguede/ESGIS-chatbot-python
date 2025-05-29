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
