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
    
    async def get_conversation(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Récupère l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
            
        Returns:
            Liste de messages avec expéditeur et contenu
        """
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'CHAT#{chat_id}',
                    ':sk_prefix': 'MSG#'
                }
            )
            
            # Convertir les résultats en format attendu
            conversation = []
            for item in response.get('Items', []):
                conversation.append({
                    'from': item.get('From', ''),
                    'content': item.get('Content', '')
                })
            
            # Trier par timestamp (SK contient le timestamp)
            conversation.sort(key=lambda x: x.get('SK', ''))
            
            return conversation
        except ClientError as e:
            print(f"Erreur lors de la récupération de la conversation depuis DynamoDB: {e}")
            return []
    
    async def reset_conversation(self, chat_id: int) -> None:
        """
        Réinitialise/efface l'historique de conversation pour un chat spécifique.
        
        Args:
            chat_id: ID du chat Telegram
        """
        try:
            # Récupérer tous les éléments à supprimer
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'CHAT#{chat_id}',
                    ':sk_prefix': 'MSG#'
                },
                ProjectionExpression='PK, SK'
            )
            
            # Supprimer chaque élément
            with self.table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'PK': item['PK'],
                            'SK': item['SK']
                        }
                    )
        except ClientError as e:
            print(f"Erreur lors de la réinitialisation de la conversation dans DynamoDB: {e}")
            raise
