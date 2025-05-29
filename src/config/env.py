"""
Configuration centralisée pour les variables d'environnement.
Toutes les variables d'environnement doivent être accessibles via cet objet.
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration centralisée pour les variables d'environnement"""
    
    # Configuration du serveur
    PORT = int(os.getenv('PORT', '3000'))
    ENV = os.getenv('ENV', 'development')
    
    # Configuration de Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Configuration de Mistral AI
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
    MISTRAL_BASE_URL = 'https://api.mistral.ai/v1'
    MISTRAL_MODEL = 'mistral-medium'
    
    # Configuration de la base de données
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    USE_MEMORY_ADAPTER = os.getenv('USE_MEMORY_ADAPTER', 'false').lower() == 'true'
    
    # MongoDB (optionnel)
    MONGODB_URI = os.getenv('MONGODB_URI', '')
    
    # DynamoDB (optionnel)
    AWS_REGION = os.getenv('AWS_REGION', 'eu-west-3')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    DYNAMO_TABLE = os.getenv('DYNAMO_TABLE', '')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'esgis_profile')
    ENV_NAME = os.getenv('ENV_NAME', 'tleguede-dev')
    IS_LAMBDA_ENVIRONMENT = bool(os.getenv('AWS_LAMBDA_FUNCTION_NAME', ''))

# Créer une instance de la configuration
config = Config()

def validate_env():
    """
    Vérifie que les variables d'environnement requises sont définies.
    
    Returns:
        list: Liste des variables d'environnement manquantes
    """
    missing_vars = []
    
    # Vérifier les variables d'environnement requises
    if not config.TELEGRAM_BOT_TOKEN:
        missing_vars.append('TELEGRAM_BOT_TOKEN')
    
    if not config.MISTRAL_API_KEY:
        missing_vars.append('MISTRAL_API_KEY')
    
    # Vérifier les variables de base de données en fonction de l'adaptateur
    if not config.USE_MEMORY_ADAPTER:
        if config.IS_LAMBDA_ENVIRONMENT and not config.DYNAMO_TABLE:
            missing_vars.append('DYNAMO_TABLE')
        elif not config.IS_LAMBDA_ENVIRONMENT and not config.DATABASE_URL:
            missing_vars.append('DATABASE_URL')
    
    return missing_vars
