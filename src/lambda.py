"""
Point d'entrée pour AWS Lambda.
"""
import json
import logging
from mangum import Mangum

from .app import create_app
from .config.env import config

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = create_app()

# Créer le gestionnaire Lambda
handler = Mangum(app)


def lambda_handler(event, context):
    """
    Fonction de gestionnaire Lambda.
    
    Args:
        event: Événement Lambda
        context: Contexte Lambda
        
    Returns:
        Réponse de l'API
    """
    # Log l'événement pour le débogage
    logger.info(f"Événement Lambda reçu: {json.dumps(event)}")
    
    # Vérifier si c'est un événement API Gateway
    if 'httpMethod' in event:
        # Utiliser Mangum pour gérer la requête
        return handler(event, context)
    
    # Vérifier si c'est un événement Telegram (via SNS ou autre)
    if 'body' in event and isinstance(event['body'], str):
        try:
            body = json.loads(event['body'])
            if 'message' in body or 'callback_query' in body:
                # C'est une mise à jour Telegram, la traiter
                logger.info("Mise à jour Telegram reçue")
                # Le traitement est géré par le bot Telegram
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'ok'})
                }
        except json.JSONDecodeError:
            logger.error("Impossible de décoder le corps de la requête en JSON")
    
    # Événement non géré
    logger.warning(f"Type d'événement non géré: {event}")
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Type d\'événement non pris en charge'})
    }
