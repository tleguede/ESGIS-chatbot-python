"""
Point d'entrée pour AWS Lambda.
"""
import json
import logging
import traceback
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
            
            logger.info("Corps de la requête: %s", json.dumps(body)[:500])  # Limiter la taille du log
            
            if 'message' in body or 'callback_query' in body or 'update_id' in body:
                logger.info("Mise à jour Telegram reçue")
                # Le traitement est géré par le bot Telegram via l'application FastAPI
                response = handler(event, context)
                logger.info("Réponse du gestionnaire: %s", response)
                return response
        
        # Si on arrive ici, c'est qu'aucun gestionnaire n'a été trouvé
        logger.warning("Aucun gestionnaire approprié trouvé pour cet événement")
        
        # Essayer de passer l'événement à Mangum quand même, au cas où
        try:
            logger.info("Tentative de traitement avec Mangum")
            return handler(event, context)
        except Exception as e:
            logger.exception("Échec du traitement avec Mangum")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Erreur lors du traitement de la requête', 'details': str(e)})
            }
    
    except Exception as e:
        # Log détaillé de l'erreur avec traceback complet
        error_id = hash(str(e)) % 10000  # Identifiant simple pour retrouver l'erreur dans les logs
        logger.exception(f"Erreur inattendue dans le gestionnaire Lambda [ID: {error_id}]")
        logger.error(f"Traceback complet: {traceback.format_exc()}")
        
        # Retourner une réponse d'erreur avec l'ID pour faciliter le débogage
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # Pour éviter les problèmes CORS
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({
                'error': 'Erreur interne du serveur', 
                'error_id': str(error_id),
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
