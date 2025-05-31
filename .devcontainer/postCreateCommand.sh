#!/bin/bash
set -e

echo "🚀 Configuration de l'environnement GitHub Codespaces pour ESGIS Chatbot..."

# Installer les dépendances Python
echo "📦 Installation des dépendances Python..."
pip install -r requirements.txt

# Configurer les variables d'environnement si elles n'existent pas
if [ ! -f .env ]; then
  echo "🔧 Création du fichier .env à partir de .env.example..."
  cp .env.example .env
  echo "⚠️ N'oubliez pas de configurer vos variables d'environnement dans le fichier .env"
fi

# Installer AWS SAM CLI si nécessaire
if ! command -v sam &> /dev/null; then
  echo "🔧 Installation de AWS SAM CLI..."
  pip install aws-sam-cli
fi

# Créer un alias pour faciliter l'utilisation de SAM
echo "alias sam-local='bash -c \"sam local start-api --port 3000\"'" >> ~/.bashrc

echo "✅ Configuration terminée! Votre environnement est prêt."
echo ""
echo "📋 Commandes utiles:"
echo "  • python -m src.app              : Démarrer l'application en mode développement"
echo "  • sam-local                      : Démarrer l'API avec SAM local"
echo "  • sam build                      : Construire l'application pour déploiement"
echo "  • sam deploy --guided            : Déployer sur AWS (nécessite configuration AWS)"
echo ""
echo "📚 Documentation: https://github.com/votre-repo/ESGIS-chatbot-python#readme"
