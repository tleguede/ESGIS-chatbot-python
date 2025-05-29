"""
Adaptateur de base de données DynamoDB pour le chatbot Telegram.
"""
import time
import boto3
from typing import Dict, List, Any
from botocore.exceptions import ClientError
from ..db_adapter import DatabaseAdapter
from ...config.env import config


class DynamoAdapter(DatabaseAdapter):
    """
    Implémentation de l'adaptateur de base de données qui utilise AWS DynamoDB.
    Optimisé pour les environnements serverless comme AWS Lambda.
    """
    
    def __init__(self):
        """Initialise l'adaptateur de base de données DynamoDB."""
        # Configurer le client DynamoDB
        if config.IS_LAMBDA_ENVIRONMENT:
            # En environnement Lambda, on utilise le rôle IAM attaché
            self.dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
        else:
            # En local, on utilise les credentials AWS
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=config.AWS_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
        self.table_name = config.DYNAMO_TABLE
        self.table = self.dynamodb.Table(self.table_name)
    
    async def save_message(self, chat_id: int, username: str, message: str) -> None:
        """
        Sauvegarde un message utilisateur dans DynamoDB.
        
        Args:
            chat_id: ID du chat Telegram
            username: Nom d'utilisateur Telegram
            message: Contenu du message
        """
        timestamp = int(time.time() * 1000)  # Timestamp en millisecondes
        
        try:
            self.table.put_item(
                Item={
                    'PK': f'CHAT#{chat_id}',
                    'SK': f'MSG#{timestamp}',
                    'Type': 'Message',
                    'From': 'user',
                    'Username': username,
                    'Content': message,
                    'Timestamp': timestamp
                }
            )
        except ClientError as e:
            print(f"Erreur lors de la sauvegarde du message dans DynamoDB: {e}")
            raise
    
    async def save_response(self, chat_id: int, response: str) -> None:
        """
        Sauvegarde une réponse du bot dans DynamoDB.
        
        Args:
            chat_id: ID du chat Telegram
            response: Contenu de la réponse
        """
        timestamp = int(time.time() * 1000)  # Timestamp en millisecondes
        
        try:
            self.table.put_item(
                Item={
                    'PK': f'CHAT#{chat_id}',
                    'SK': f'MSG#{timestamp}',
                    'Type': 'Message',
                    'From': 'assistant',
                    'Content': response,
                    'Timestamp': timestamp
                }
            )
        except ClientError as e:
            print(f"Erreur lors de la sauvegarde de la réponse dans DynamoDB: {e}")
            raise
    
    async def get_conversation(self, chat_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """
        Récupère l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
            limit: Nombre maximum de messages à récupérer (par défaut: 10)
            
        Returns:
            Liste de messages avec expéditeur et contenu
        """
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'CHAT#{chat_id}',
                    ':sk_prefix': 'MSG#'
                },
                Limit=limit,
                ScanIndexForward=False,  # Pour obtenir les messages les plus récents en premier
                ConsistentRead=True
            )
            
            # Convertir les éléments DynamoDB en format standard
            messages = []
            for item in response.get('Items', []):
                messages.append({
                    'from': 'assistant' if item.get('is_bot', False) else 'user',
                    'content': item.get('content', '')
                })
            
            # Inverser pour avoir l'ordre chronologique
            return messages[::-1]
            
        except ClientError as e:
            print(f"Erreur lors de la récupération de la conversation: {e}")
            return []
    
    async def reset_conversation(self, chat_id: int) -> None:
        """
        Réinitialise la conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
        """
        try:
            # Supprimer tous les messages du chat
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'CHAT#{chat_id}'
                }
            )
            
            # Supprimer chaque message
            with self.table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'PK': item['PK'],
                            'SK': item['SK']
                        }
                    )
                    
        except ClientError as e:
            print(f"Erreur lors de la réinitialisation de la conversation: {e}")
            raise
