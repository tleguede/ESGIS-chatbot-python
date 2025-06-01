"""
Point d'entrée pour AWS Lambda.
"""
import json
import logging
import os
import traceback
import uuid
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


# Définir les headers CORS pour les réponses d'erreur
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': '*'
}

def lambda_handler(event, context):
    """
    Fonction de gestionnaire Lambda.
    
    Args:
        event: Événement Lambda
        context: Contexte Lambda
        
    Returns:
        Réponse de l'API
    """
    # Afficher des informations de débogage sur l'environnement
    logger.info(f"Démarrage du gestionnaire Lambda avec timeout restant: {context.get_remaining_time_in_millis()/1000:.2f}s")
    logger.info(f"Variables d'environnement: API_URL={os.environ.get('API_URL')}, ENV={os.environ.get('ENV')}")
    
    # Vérifier rapidement si nous sommes dans un cold start
    if not hasattr(lambda_handler, "_initialized"):
        logger.info("Cold start détecté - Première exécution de la fonction")
        lambda_handler._initialized = True
    else:
        logger.info("Warm start - La fonction a déjà été initialisée")
    
    try:
        # Log l'événement pour le débogage (version sécurisée qui ne log pas les données sensibles)
        logger.info("Type d'événement reçu: %s", type(event).__name__)
        logger.debug("Événement complet: %s", json.dumps(event))
        
        # Vérifier si c'est un événement API Gateway V2 (HTTP API)
        if 'version' in event and event.get('version') == '2.0':
            logger.info("Événement API Gateway V2 détecté")
            return handler(event, context)
            
        # Vérifier si c'est un événement API Gateway V1 (REST API)
        if 'httpMethod' in event and 'resource' in event:
            logger.info("Événement API Gateway V1 détecté")
            return handler(event, context)
        
        # Vérifier si c'est un événement direct depuis API Gateway
        if 'requestContext' in event and 'http' in event['requestContext']:
            logger.info("Événement API Gateway direct détecté")
            return handler(event, context)
        
        # Vérifier si c'est un événement Telegram (via API Gateway ou autre)
        if 'body' in event:
            body = event['body']
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    logger.error("Impossible de décoder le corps de la requête en JSON")
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Invalid JSON format'})
                    }
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Type d'événement non pris en charge"}),
                "headers": CORS_HEADERS
            }
    except Exception as e:
        # Générer un ID d'erreur unique pour faciliter le débogage
        error_id = str(uuid.uuid4())
        error_details = traceback.format_exc()
        
        # Journaliser l'erreur avec l'ID pour référence
        logger.error(f"Erreur non gérée (ID: {error_id}): {str(e)}")
        logger.error(f"Détails: {error_details}")
        
        # Retourner une réponse d'erreur avec l'ID pour référence
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'Erreur interne du serveur', 
                'error_id': error_id,
                'message': str(e)
            })
        }
    
    # Événement non géré
    logger.warning("Type d'événement non géré")
    return {
        'statusCode': 400,
        'body': json.dumps({
            'error': 'Type d\'événement non pris en charge',
            'event_type': type(event).__name__,
            'event_keys': list(event.keys()) if hasattr(event, 'keys') else 'N/A'
        })
    }
