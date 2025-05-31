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
                    # Gérer les commandes - traitement direct sans passer par les handlers
                    if text == '/start':
                        welcome_message = 'Bonjour ! Je suis votre assistant IA alimenté par Mistral AI. Comment puis-je vous aider aujourd\'hui?\n\n' \
                                      'Utilisez /chat pour démarrer une conversation avec moi\n' \
                                      'Utilisez /reset pour effacer notre historique de conversation\n' \
                                      'Utilisez /help pour voir toutes les commandes disponibles'
                        
                        # Envoyer directement un message via l'API Telegram
                        await self.telegram_service.send_message(chat_id, welcome_message)
                    
                    elif text == '/chat':
                        # Activer le mode chat pour cet utilisateur
                        self.telegram_service.chat_mode[chat_id] = True
                        await self.telegram_service.send_message(chat_id, 'Mode chat activé ! Vous pouvez maintenant me parler directement. Que voulez-vous discuter ?')
                    
                    elif text == '/reset':
                        # Réinitialiser la conversation
                        await self.telegram_service.db_adapter.reset_conversation(chat_id)
                        await self.telegram_service.send_message(chat_id, 'Votre historique de conversation a été réinitialisé.')
                    
                    elif text == '/help':
                        help_message = 'Commandes disponibles:\n\n' \
                                   '/start - Démarrer la conversation et afficher le menu\n' \
                                   '/chat - Commencer à discuter avec l\'IA\n' \
                                   '/reset - Réinitialiser votre historique de conversation\n' \
                                   '/help - Afficher ce message d\'aide'
                        await self.telegram_service.send_message(chat_id, help_message)
                else:
                    # Traiter comme un message texte normal
                    response = await self.telegram_service.process_message(chat_id, username, text)
                    # Envoyer la réponse via l'API Telegram
                    await self.telegram_service.send_message(chat_id, response)
            
            # Gérer les callbacks des boutons inline
            elif 'callback_query' in update:
                callback_query = update['callback_query']
                message = callback_query['message']
                chat_id = message['chat']['id']
                username = callback_query['from'].get('username', 'inconnu')
                data = callback_query.get('data', '')
                
                # Traiter le callback directement
                if data == "feedback_positive":
                    await self.telegram_service.send_message(chat_id, "Merci pour votre feedback positif ! 😊")
                elif data == "feedback_negative":
                    await self.telegram_service.send_message(chat_id, "Je suis désolé que ma réponse n'ait pas été utile. Comment puis-je m'améliorer ?")
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la mise à jour: {str(e)}")
            logger.error(f"Détails de l'erreur: {str(e.__traceback__)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du traitement de la mise à jour: {str(e)}"
            )
