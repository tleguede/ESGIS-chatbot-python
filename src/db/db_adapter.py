"""
Interface d'adaptateur de base de données pour le chatbot Telegram.
Toutes les implémentations de base de données doivent implémenter cette interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DatabaseAdapter(ABC):
    """
    Interface d'adaptateur de base de données pour le chatbot Telegram.
    Toutes les implémentations de base de données doivent implémenter cette interface.
    """
    
    @abstractmethod
    async def save_message(self, chat_id: int, username: str, message: str) -> None:
        """
        Sauvegarde un message utilisateur dans la base de données.
        
        Args:
            chat_id: ID du chat Telegram
            username: Nom d'utilisateur Telegram
            message: Contenu du message
        """
        pass
    
    @abstractmethod
    async def save_response(self, chat_id: int, response: str) -> None:
        """
        Sauvegarde une réponse du bot dans la base de données.
        
        Args:
            chat_id: ID du chat Telegram
            response: Contenu de la réponse
        """
        pass
    
    @abstractmethod
    async def get_conversation(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Récupère l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
            
        Returns:
            Liste de messages avec expéditeur et contenu
        """
        pass
    
    @abstractmethod
    async def reset_conversation(self, chat_id: int) -> None:
        """
        Réinitialise/efface l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
        """
        pass
