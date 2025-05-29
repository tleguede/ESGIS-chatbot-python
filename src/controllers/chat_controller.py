"""
Contrôleur pour gérer les requêtes de chat via l'API.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from ..services.telegram_service import TelegramService

# Configuration du logger
logger = logging.getLogger(__name__)


class MessageRequest(BaseModel):
    """Modèle de requête pour envoyer un message."""
    chat_id: int
    username: str
    message: str


class MessageResponse(BaseModel):
    """Modèle de réponse pour un message."""
    response: str


class ChatController:
    """Contrôleur pour gérer les requêtes de chat via l'API."""
    
    def __init__(self, telegram_service: TelegramService):
        """
        Initialise le contrôleur de chat.
        
        Args:
            telegram_service: Service Telegram à utiliser
        """
        self.telegram_service = telegram_service
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """
        Envoie un message au bot et retourne la réponse.
        
        Args:
            request: Requête contenant les informations du message
            
        Returns:
            Réponse du bot
        """
        try:
            response = await self.telegram_service.process_message(
                request.chat_id,
                request.username,
                request.message
            )
            
            return MessageResponse(response=response)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du message: {str(e)}")
    
    async def get_health(self) -> Dict[str, str]:
        """
        Vérifie l'état de santé du service.
        
        Returns:
            État de santé du service
        """
        return {"status": "ok"}
        
    async def handle_webhook_update(self, update: Dict[str, Any]) -> Dict[str, str]:
        """
        Traite une mise à jour du webhook Telegram.
        
        Args:
            update: Données de mise à jour de Telegram
            
        Returns:
            Réponse de confirmation
        """
        try:
            # Vérifier si c'est un message
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                username = message['from'].get('username', 'inconnu')
                text = message.get('text', '')
                
                if text.startswith('/'):
                    # Gérer les commandes
                    if text == '/start':
                        await self.telegram_service._start_command(update, None)
                    elif text == '/chat':
                        await self.telegram_service._chat_command(update, None)
                    elif text == '/reset':
                        await self.telegram_service._reset_command(update, None)
                    elif text == '/help':
                        await self.telegram_service._help_command(update, None)
                else:
                    # Traiter comme un message texte normal
                    await self.telegram_service.process_message(chat_id, username, text)
            
            # Gérer les callbacks des boutons inline
            elif 'callback_query' in update:
                callback_query = update['callback_query']
                message = callback_query['message']
                chat_id = message['chat']['id']
                username = callback_query['from'].get('username', 'inconnu')
                data = callback_query.get('data', '')
                
                # Traiter le callback
                await self.telegram_service.process_callback(callback_query)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la mise à jour: {str(e)}")
            logger.error(f"Détails de l'erreur: {str(e.__traceback__)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du traitement de la mise à jour: {str(e)}"
            )
