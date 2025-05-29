"""
Routes pour l'API de chat.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import os
import requests

from ..config.env import config
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
    
    @router.post("/webhook")
    async def set_webhook() -> Dict[str, str]:
        """
        Configure le webhook Telegram pour recevoir les mises à jour.
        
        Returns:
            Statut de la configuration du webhook
        """
        try:
            # Obtenir l'URL de l'API depuis les variables d'environnement
            api_url = os.getenv('API_URL')
            if not api_url:
                raise HTTPException(
                    status_code=500,
                    detail="API_URL n'est pas configuré dans les variables d'environnement"
                )
            
            # Construire l'URL du webhook
            webhook_url = f"{api_url.rstrip('/')}/api/chat/update"
            
            # Configurer le webhook avec Telegram
            response = requests.post(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": webhook_url}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erreur lors de la configuration du webhook: {response.text}"
                )
                
            return {"status": "success", "webhook_url": webhook_url}
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la configuration du webhook: {str(e)}"
            )
    
    @router.post("/update")
    async def handle_update(request: Request):
        """
        Point d'entrée pour les mises à jour du webhook Telegram.
        """
        try:
            update = await request.json()
            return await chat_controller.handle_webhook_update(update)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return router
