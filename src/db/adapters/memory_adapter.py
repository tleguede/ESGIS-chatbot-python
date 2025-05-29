"""
Adaptateur de base de données en mémoire pour le chatbot Telegram.
"""
from typing import Dict, List, Any
from ..db_adapter import DatabaseAdapter


class MemoryAdapter(DatabaseAdapter):
    """
    Implémentation de l'adaptateur de base de données qui stocke les conversations en mémoire.
    Utile pour le développement et les tests.
    """
    
    def __init__(self):
        """Initialise l'adaptateur de base de données en mémoire."""
        # Dictionnaire pour stocker les conversations par chat_id
        self.conversations: Dict[int, List[Dict[str, str]]] = {}
    
    async def save_message(self, chat_id: int, username: str, message: str) -> None:
        """
        Sauvegarde un message utilisateur dans la mémoire.
        
        Args:
            chat_id: ID du chat Telegram
            username: Nom d'utilisateur Telegram
            message: Contenu du message
        """
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []
        
        self.conversations[chat_id].append({
            'from': 'user',
            'content': message
        })
    
    async def save_response(self, chat_id: int, response: str) -> None:
        """
        Sauvegarde une réponse du bot dans la mémoire.
        
        Args:
            chat_id: ID du chat Telegram
            response: Contenu de la réponse
        """
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []
        
        self.conversations[chat_id].append({
            'from': 'assistant',
            'content': response
        })
    
    async def get_conversation(self, chat_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """
        Récupère l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
            limit: Nombre maximum de messages à récupérer (par défaut: 10)
            
        Returns:
            Liste de messages avec expéditeur et contenu
        """
        messages = self.conversations.get(chat_id, [])
        # Retourne les 'limit' derniers messages
        return messages[-limit:] if limit > 0 else messages
    
    async def reset_conversation(self, chat_id: int) -> None:
        """
        Réinitialise/efface l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
        """
        if chat_id in self.conversations:
            self.conversations[chat_id] = []
