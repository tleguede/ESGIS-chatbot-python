"""
Handler Lambda pour l'application FastAPI.
Ce module adapte notre application FastAPI pour fonctionner dans AWS Lambda.
"""
import logging
import os
from mangum import Mangum
from .app import app, setup_webhook

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Créer un gestionnaire Lambda
handler = Mangum(app)

# Configurer le webhook au démarrage de la fonction Lambda
def configure_webhook_on_cold_start():
    """
    Configure le webhook Telegram lors du démarrage à froid de la fonction Lambda.
    Cette fonction est exécutée une seule fois lors du démarrage à froid.
    """
    try:
        # Vérifier si nous sommes dans un environnement Lambda
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            logger.info("Configuration du webhook Telegram dans l'environnement Lambda...")
            
            # Récupérer l'URL de l'API depuis les variables d'environnement
            api_url = os.environ.get('API_URL')
            
            if not api_url:
                logger.warning("API_URL non définie. Le webhook ne sera pas configuré.")
                return
            
            # Configurer le webhook de manière asynchrone
            import asyncio
            
            # Créer une nouvelle boucle d'événements
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Exécuter la configuration du webhook
            loop.run_until_complete(setup_webhook())
            
            logger.info("Webhook Telegram configuré avec succès.")
        else:
            logger.info("Non exécuté dans Lambda, ignorant la configuration du webhook.")
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du webhook: {str(e)}")

# Exécuter la configuration du webhook lors du démarrage à froid
configure_webhook_on_cold_start()
