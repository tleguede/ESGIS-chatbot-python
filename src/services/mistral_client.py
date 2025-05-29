"""
Client pour interagir avec l'API Mistral AI.
"""
import requests
from typing import List, Dict, Any
import logging
from ..config.env import config

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MistralClient:
    """Client pour interagir avec l'API Mistral AI."""
    
    def __init__(self):
        """Initialise le client Mistral AI."""
        self.api_key = config.MISTRAL_API_KEY
        self.base_url = config.MISTRAL_BASE_URL
        self.model = config.MISTRAL_MODEL
        
        if not self.api_key:
            logger.warning('MISTRAL_API_KEY n\'est pas défini dans les variables d\'environnement')
    
    async def get_completion(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Envoie un message à Mistral AI et obtient une réponse.
        
        Args:
            prompt: Le message de l'utilisateur
            conversation_history: Historique de conversation précédent pour le contexte
            
        Returns:
            La réponse de l'IA
        """
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Formater l'historique de conversation pour l'API Mistral
            messages = self._format_conversation_history(conversation_history)
            
            # Ajouter le message utilisateur actuel
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Appeler l'API Mistral
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    'model': self.model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }
            )
            
            # Vérifier si la requête a réussi
            response.raise_for_status()
            
            # Extraire et retourner la réponse
            return response.json()['choices'][0]['message']['content']
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'appel à l'API Mistral: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Réponse de l'API: {e.response.text}")
            return "Désolé, j'ai rencontré une erreur lors du traitement de votre demande."
    
    def _format_conversation_history(self, conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Formate l'historique de conversation pour l'API Mistral.
        
        Args:
            conversation_history: Tableau de messages avec expéditeur et contenu
            
        Returns:
            Messages formatés pour l'API Mistral
        """
        return [
            {
                'role': 'user' if message['from'] == 'user' else 'assistant',
                'content': message['content']
            }
            for message in conversation_history
        ]
