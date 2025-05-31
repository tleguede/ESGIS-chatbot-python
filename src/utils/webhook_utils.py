"""
Utilitaires pour la gestion des webhooks Telegram.
"""
import asyncio
import logging
from typing import Dict, Optional, Tuple
import requests
from ..config.env import config

# Configuration du logger
logger = logging.getLogger(__name__)

class WebhookConfig:
    """Configuration pour la gestion des webhooks."""
    
    def __init__(self, token: str, base_url: str, endpoint: str = "/api/chat/update"):
        """
        Initialise la configuration du webhook.
        
        Args:
            token: Token du bot Telegram
            base_url: URL de base de l'API (sans le endpoint)
            endpoint: Endpoint pour les mises à jour (par défaut: "/api/chat/update")
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.endpoint = endpoint.lstrip('/')
        self.webhook_url = f"{self.base_url}/{self.endpoint}"


def get_webhook_info(token: Optional[str] = None) -> Dict:
    """
    Récupère les informations sur le webhook actuel.
    
    Args:
        token: Token du bot Telegram (optionnel, utilise config.TELEGRAM_BOT_TOKEN par défaut)
        
    Returns:
        Dict: Réponse de l'API Telegram ou None en cas d'erreur
    """
    token = token or config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("Aucun token Telegram n'a été fourni et TELEGRAM_BOT_TOKEN n'est pas défini")
        return {}
    
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getWebhookInfo",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        logger.warning(f"Échec de la récupération du webhook: {response.text}")
        return {}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos du webhook: {str(e)}")
        return {}


async def delete_webhook(token: Optional[str] = None) -> Tuple[bool, str]:
    """
    Supprime le webhook existant.
    
    Args:
        token: Token du bot Telegram (optionnel, utilise config.TELEGRAM_BOT_TOKEN par défaut)
        
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    token = token or config.TELEGRAM_BOT_TOKEN
    if not token:
        error_msg = "Aucun token Telegram n'a été fourni et TELEGRAM_BOT_TOKEN n'est pas défini"
        logger.error(error_msg)
        return False, error_msg
    
    # Vérifier d'abord s'il y a un webhook actif
    webhook_info = get_webhook_info(token)
    if not webhook_info.get('result', {}).get('url'):
        return True, "Aucun webhook actif détecté"
    
    try:
        logger.info(f"Suppression du webhook actuel: {webhook_info['result']['url']}")
        response = requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok') and result.get('result'):
                logger.info("✅ Webhook supprimé avec succès")
                return True, result.get('description', 'Webhook supprimé avec succès')
            
        error_msg = f"Échec de la suppression du webhook: {response.text}"
        logger.error(error_msg)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Erreur lors de la suppression du webhook: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


async def setup_webhook(token: Optional[str] = None, base_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    Configure le webhook Telegram.
    
    Args:
        token: Token du bot Telegram (optionnel, utilise config.TELEGRAM_BOT_TOKEN par défaut)
        base_url: URL de base pour le webhook (optionnel, utilise config.API_URL par défaut)
        
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    token = token or config.TELEGRAM_BOT_TOKEN
    base_url = base_url or config.API_URL
    
    if not token or not base_url:
        error_msg = "Token Telegram ou URL de base manquant"
        logger.error(error_msg)
        return False, error_msg
    
    # Créer la configuration du webhook
    webhook_config = WebhookConfig(token, base_url)
    
    # Supprimer d'abord tout webhook existant
    success, message = await delete_webhook(token)
    if not success and "Aucun webhook actif détecté" not in message:
        return False, f"Échec de la suppression du webhook existant: {message}"
    
    try:
        # Configurer le nouveau webhook
        logger.info(f"Configuration du nouveau webhook vers: {webhook_config.webhook_url}")
        response = requests.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={
                "url": webhook_config.webhook_url,
                "max_connections": 40,
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok') and result.get('result'):
                logger.info(f"✅ Webhook configuré avec succès vers {webhook_config.webhook_url}")
                return True, result.get('description', 'Webhook configuré avec succès')
        
        error_msg = f"Échec de la configuration du webhook: {response.text}"
        logger.error(error_msg)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Erreur lors de la configuration du webhook: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
