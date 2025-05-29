"""
Application principale pour le chatbot Telegram.
"""
import asyncio
import logging
import os
import requests
from fastapi import FastAPI
from typing import Optional

from .config.env import config, validate_env
from .config.swagger import setup_swagger
from .db.db_adapter import DatabaseAdapter
from .db.adapters.memory_adapter import MemoryAdapter
from .db.adapters.dynamo_adapter import DynamoAdapter
from .services.telegram_service import TelegramService
from .controllers.chat_controller import ChatController
from .routes.chat_route import create_chat_router

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_database_adapter() -> DatabaseAdapter:
    """
    Obtient l'adaptateur de base de données approprié en fonction des variables d'environnement.
    
    Returns:
        Adaptateur de base de données configuré
    """
    # Vérifier si nous devons utiliser l'adaptateur mémoire
    if config.USE_MEMORY_ADAPTER:
        logger.info("Utilisation de l'adaptateur mémoire pour le stockage de la base de données")
        return MemoryAdapter()
    
    # Vérifier si nous devons utiliser DynamoDB (environnement AWS Lambda)
    if config.IS_LAMBDA_ENVIRONMENT:
        logger.info("Utilisation de l'adaptateur DynamoDB pour le stockage de la base de données")
        return DynamoAdapter()
    
    # Par défaut, utiliser l'adaptateur mémoire
    logger.info("Utilisation de l'adaptateur mémoire par défaut")
    return MemoryAdapter()


def create_app(db_adapter: Optional[DatabaseAdapter] = None) -> FastAPI:
    """
    Crée et configure l'application FastAPI.
    
    Args:
        db_adapter: Adaptateur de base de données à utiliser (optionnel)
        
    Returns:
        Instance de l'application FastAPI configurée
    """
    # Valider les variables d'environnement
    missing_vars = validate_env()
    if missing_vars:
        logger.warning(f"Variables d'environnement manquantes : {', '.join(missing_vars)}")
    
    # Utiliser l'adaptateur fourni ou en créer un nouveau
    if db_adapter is None:
        db_adapter = get_database_adapter()
    
    # Créer l'application FastAPI
    app = FastAPI(
        title="Chatbot API",
        description="API pour le chatbot Telegram",
        version="1.0.0"
    )
    
    # Configurer la documentation Swagger
    setup_swagger(app)
    
    # Initialiser le service Telegram
    telegram_service = TelegramService(db_adapter)
    
    # Initialiser le contrôleur de chat
    chat_controller = ChatController(telegram_service)
    
    # Créer et enregistrer le routeur de chat
    chat_router = create_chat_router(chat_controller)
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    
    # Configurer le webhook au démarrage si en production
    @app.on_event("startup")
    async def startup_event():
        if config.ENV == "production" or config.IS_LAMBDA_ENVIRONMENT:
            try:
                # Obtenir l'URL de l'API depuis les variables d'environnement
                api_url = os.getenv('API_URL')
                if not api_url:
                    logger.warning("API_URL n'est pas défini, impossible de configurer le webhook")
                    return
                
                # Configurer le webhook
                webhook_url = f"{api_url.rstrip('/')}/api/chat/update"
                response = requests.post(
                    f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/setWebhook",
                    json={"url": webhook_url}
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook configuré avec succès vers {webhook_url}")
                else:
                    logger.error(f"Échec de la configuration du webhook: {response.text}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la configuration du webhook: {str(e)}")
    
    # Ajouter un événement de démarrage pour lancer le bot Telegram
    @app.on_event("startup")
    async def startup_event():
        # Vérifier que les variables d'environnement requises sont définies
        missing_vars = validate_env()
        if missing_vars:
            logger.error(f"Variables d'environnement manquantes : {', '.join(missing_vars)}")
            logger.error("Veuillez définir ces variables dans le fichier .env")
            return
        
        # Démarrer le bot Telegram en mode polling (seulement en mode serveur)
        if not config.IS_LAMBDA_ENVIRONMENT:
            asyncio.create_task(telegram_service.start_polling())
            logger.info(f"Serveur démarré sur le port {config.PORT}")
            logger.info(f"Documentation API disponible à http://localhost:{config.PORT}")
            logger.info("Le bot Telegram est actif et écoute les messages")
    
    # Ajouter un événement d'arrêt pour arrêter le bot Telegram
    @app.on_event("shutdown")
    async def shutdown_event():
        if not config.IS_LAMBDA_ENVIRONMENT:
            await telegram_service.stop()
    
    return app
