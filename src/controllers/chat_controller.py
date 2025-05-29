"""
Contrôleur pour gérer les requêtes de chat via l'API.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from ..services.telegram_service import TelegramService


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
        return {"status": "ok", "message": "Le service de chat est opérationnel"}
