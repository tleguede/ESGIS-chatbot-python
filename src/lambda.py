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

# Utiliser un singleton pour l'application FastAPI afin d'éviter les problèmes de "warm start"
_app = None
_handler = None

def get_application():
    """Retourne l'instance singleton de l'application FastAPI."""
    global _app
    if _app is None:
        logger.info("Initialisation de l'application FastAPI (première fois ou après cold start)")
        _app = create_app()
    return _app

def get_handler():
    """Retourne l'instance singleton du gestionnaire Mangum."""
    global _handler
    if _handler is None:
        _handler = Mangum(get_application())
    return _handler


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
    # Générer un ID unique pour cette requête pour faciliter le suivi dans les logs
    request_id = str(uuid.uuid4())[:8]
    
    # Afficher des informations de débogage sur l'environnement
    logger.info(f"[{request_id}] Démarrage du gestionnaire Lambda avec timeout restant: {context.get_remaining_time_in_millis()/1000:.2f}s")
    logger.info(f"[{request_id}] Variables d'environnement: API_URL={os.environ.get('API_URL')}, ENV={os.environ.get('ENV')}")
    
    # Vérifier rapidement si nous sommes dans un cold start
    if not hasattr(lambda_handler, "_initialized"):
        logger.info(f"[{request_id}] Cold start détecté - Première exécution de la fonction")
        lambda_handler._initialized = True
    else:
        logger.info(f"[{request_id}] Warm start - La fonction a déjà été initialisée")
    
    try:
        # Log l'événement pour le débogage (version sécurisée qui ne log pas les données sensibles)
        logger.info(f"[{request_id}] Type d'événement reçu: {type(event).__name__}")
        logger.debug(f"[{request_id}] Événement complet: {json.dumps(event)}")
        
        # Déterminer le type d'événement et le traiter en conséquence
        if "httpMethod" in event:  # API Gateway v1
            logger.info(f"[{request_id}] Traitement d'un événement API Gateway v1")
            return get_handler()(event, context)
            
        elif "requestContext" in event and "http" in event["requestContext"]:  # API Gateway v2
            logger.info(f"[{request_id}] Traitement d'un événement API Gateway v2")
            return get_handler()(event, context)
            
        elif "version" in event and event.get("version") == "2.0":  # API Gateway v2 format alternatif
            logger.info(f"[{request_id}] Traitement d'un événement API Gateway v2 (format alternatif)")
            return get_handler()(event, context)
            
        elif "update_id" in event:  # Événement Telegram direct
            logger.info(f"[{request_id}] Traitement d'un événement Telegram direct")
            # Traiter l'événement Telegram ici si nécessaire
            return {
                "statusCode": 200,
                "body": json.dumps({"success": True}),
                "headers": CORS_HEADERS
            }
            
        # Si c'est un autre type d'événement, essayer de le traiter comme un événement API Gateway générique
        logger.warning(f"[{request_id}] Type d'événement inconnu, tentative de traitement générique")
        try:
            return get_handler()(event, context)
        except Exception as handler_error:
            logger.error(f"[{request_id}] Échec du traitement générique: {str(handler_error)}")
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
        logger.error(f"[{request_id}] Erreur non gérée (ID: {error_id}): {str(e)}")
        logger.error(f"[{request_id}] Détails: {error_details}")
        
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
