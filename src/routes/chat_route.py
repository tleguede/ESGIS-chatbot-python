"""
Routes pour l'API de chat.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..controllers.chat_controller import ChatController, MessageRequest, MessageResponse


def create_chat_router(chat_controller: ChatController) -> APIRouter:
    """
    Crée un routeur FastAPI pour les endpoints de chat.
    
    Args:
        chat_controller: Contrôleur de chat à utiliser
        
    Returns:
        Routeur FastAPI configuré
    """
    router = APIRouter(tags=["chat"])
    
    @router.post("/send", response_model=MessageResponse)
    async def send_message(request: MessageRequest) -> MessageResponse:
        """
        Envoie un message au bot et retourne la réponse.
        
        Args:
            request: Requête contenant les informations du message
            
        Returns:
            Réponse du bot
        """
        return await chat_controller.send_message(request)
    
    @router.get("/health", response_model=Dict[str, str])
    async def health_check() -> Dict[str, str]:
        """
        Vérifie l'état de santé du service.
        
        Returns:
            État de santé du service
        """
        return await chat_controller.get_health()
    
    return router
