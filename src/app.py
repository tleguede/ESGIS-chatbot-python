"""
Application principale pour le chatbot Telegram.
"""
import asyncio
import logging
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
        Application FastAPI configurée
    """
    app = FastAPI(title="ESGIS Telegram Chatbot API")
    
    # Configurer Swagger
    setup_swagger(app)
    
    # Utiliser l'adaptateur fourni ou en obtenir un nouveau
    if db_adapter is None:
        db_adapter = get_database_adapter()
    
    # Créer les services et contrôleurs
    telegram_service = TelegramService(db_adapter)
    chat_controller = ChatController(telegram_service)
    
    # Ajouter les routes
    app.include_router(create_chat_router(chat_controller), prefix="/chat")
    
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
