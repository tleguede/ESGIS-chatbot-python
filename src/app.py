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
    # Créer l'application FastAPI avec une configuration minimale d'abord
    app = FastAPI(
        title="Chatbot API",
        description="API pour le chatbot Telegram",
        version="1.0.0"
    )
    
    # Route racine qui redirige vers la documentation (ajoutée tôt pour éviter les erreurs 500)
    from fastapi.responses import RedirectResponse
    
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirige vers la documentation de l'API."""
        return RedirectResponse(url="/docs")
    
    try:
        # Valider les variables d'environnement
        missing_vars = validate_env()
        if missing_vars:
            logger.warning(f"Variables d'environnement manquantes : {', '.join(missing_vars)}")
        
        # Utiliser l'adaptateur fourni ou en créer un nouveau
        if db_adapter is None:
            db_adapter = get_database_adapter()
            
        # Configurer la documentation Swagger
        setup_swagger(app)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'application: {str(e)}")
        # On continue quand même pour que l'application démarre, mais certaines fonctionnalités pourraient ne pas marcher
    
    # Initialiser le service Telegram
    telegram_service = TelegramService(db_adapter)
    
    # Initialiser le contrôleur de chat
    chat_controller = ChatController(telegram_service)
    
    # Créer et enregistrer le routeur de chat
    chat_router = create_chat_router(chat_controller)
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    
    async def get_webhook_info():
        """
        Récupère les informations sur le webhook actuel.
        
        Returns:
            dict: Informations du webhook ou None en cas d'erreur
        """
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getWebhookInfo",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Échec de la récupération du webhook: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du webhook: {str(e)}")
            return None

    async def delete_webhook():
        """
        Supprime le webhook existant.
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            # D'abord vérifier s'il y a un webhook actif
            webhook_info = await get_webhook_info()
            if not webhook_info or not webhook_info.get('result', {}).get('url'):
                logger.info("Aucun webhook actif détecté")
                return True
                
            logger.info(f"Suppression du webhook actuel: {webhook_info['result']['url']}")
            
            # Supprimer le webhook
            response = requests.post(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/deleteWebhook",
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Webhook supprimé avec succès")
                # Vérifier que la suppression a bien été prise en compte
                await asyncio.sleep(1)  # Petit délai pour la propagation
                webhook_info = await get_webhook_info()
                if not webhook_info or not webhook_info.get('result', {}).get('url'):
                    return True
                logger.warning("Le webhook est toujours présent après suppression")
                return False
            else:
                logger.warning(f"Échec de la suppression du webhook: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du webhook: {str(e)}")
            return False

    async def setup_webhook() -> bool:
        """
        Configure le webhook Telegram avec gestion des erreurs et nouvelles tentatives.
        
        Returns:
            bool: True si la configuration a réussi, False sinon
        """
        max_retries = 3
        retry_delay = 2  # secondes
        
        for attempt in range(max_retries):
            try:
                # Petit délai entre les tentatives
                if attempt > 0:
                    logger.info(f"⏳ Nouvelle tentative dans {retry_delay} secondes... (tentative {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                
                # 1. Vérifier l'état actuel du webhook
                logger.info("🔍 Vérification de l'état actuel du webhook...")
                webhook_info = await get_webhook_info()
                if webhook_info and webhook_info.get('result', {}).get('url'):
                    logger.info(f"ℹ️ Webhook actuel: {webhook_info['result']['url']}")
                
                # 2. Supprimer tout webhook existant
                logger.info("🗑️  Nettoyage des webhooks existants...")
                if not await delete_webhook():
                    logger.warning("⚠️  Impossible de supprimer le webhook existant")
                    continue
                
                # 3. Obtenir l'URL de l'API
                api_url = config.API_URL
                logger.info(f"🔄 Configuration du webhook avec l'URL: {api_url}")
                if not api_url:
                    logger.error("❌ API_URL n'est pas défini dans la configuration, impossible de configurer le webhook")
                    return False
                
                # 4. Configurer le nouveau webhook
                webhook_url = f"{api_url.rstrip('/')}/api/chat/update"
                logger.info(f"🔄 Configuration du nouveau webhook vers: {webhook_url}")
                
                response = requests.post(
                    f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/setWebhook",
                    json={
                        "url": webhook_url,
                        "max_connections": 40,  # Nombre maximum de connexions parallèles
                        "allowed_updates": ["message", "callback_query"]  # Types d'updates à recevoir
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Vérifier que le webhook a bien été configuré
                    await asyncio.sleep(1)
                    webhook_info = await get_webhook_info()
                    if webhook_info and webhook_info.get('result', {}).get('url') == webhook_url:
                        logger.info(f"✅ Webhook configuré avec succès vers {webhook_url}")
                        return True
                    else:
                        logger.error("❌ Le webhook n'a pas été correctement configuré")
                        continue
                
                # Gestion des erreurs spécifiques
                error_msg = response.text
                logger.error(f"❌ Échec de la configuration du webhook: {error_msg}")
                
                # Si c'est une erreur 429 (trop de requêtes), attendre plus longtemps
                if response.status_code == 429:
                    retry_after = response.json().get('parameters', {}).get('retry_after', 10)
                    logger.info(f"⏳ Attente de {retry_after} secondes avant de réessayer...")
                    await asyncio.sleep(retry_after)
            
            except Exception as e:
                logger.error(f"❌ Erreur lors de la configuration du webhook: {str(e)}")
                logger.debug(f"Détails de l'erreur: {str(e.__traceback__)}")
                
        logger.error(f"❌ Échec de la configuration du webhook après {max_retries} tentatives")
        return False

    @app.on_event("startup")
    async def startup_event():
        """Gère les événements de démarrage de l'application."""
        logger.info("\n" + "="*60)
        logger.info("🚀 Démarrage de l'application...")
        logger.info("="*60)
        
        try:
            # 1. Vérification des variables d'environnement
            missing_vars = validate_env()
            if missing_vars:
                logger.warning(f"⚠️  Variables d'environnement manquantes : {', '.join(missing_vars)}")
                logger.warning("ℹ️  Certaines fonctionnalités pourraient ne pas fonctionner correctement")
            
            # 2. Configuration du webhook si en environnement Lambda
            if config.IS_LAMBDA_ENVIRONMENT:
                logger.info("🌐 Configuration du webhook Telegram...")
                if await setup_webhook():
                    logger.info("✅ Configuration du webhook terminée avec succès")
                else:
                    logger.error("❌ Échec de la configuration du webhook")
            else:
                # 3. Mode développement : Démarrer le bot en mode polling
                logger.info("🔍 Mode développement : démarrage en mode polling...")
                try:
                    await telegram_service.start_polling()
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🚀 Serveur démarré sur http://localhost:{config.PORT}")
                    logger.info(f"📚 Documentation API : http://localhost:{config.PORT}/docs")
                    logger.info(f"🤖 Bot Telegram en écoute sur le chat")
                    logger.info(f"{'='*60}\n")
                except Exception as e:
                    logger.error(f"❌ Erreur lors du démarrage du bot Telegram: {str(e)}")
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Erreur critique au démarrage: {str(e)}")
            logger.error("L'application continue de fonctionner mais certaines fonctionnalités pourraient être affectées")
    
    # Ajouter un événement d'arrêt pour arrêter le bot Telegram
    @app.on_event("shutdown")
    async def shutdown_event():
        if not config.IS_LAMBDA_ENVIRONMENT:
            await telegram_service.stop()
    
    return app
