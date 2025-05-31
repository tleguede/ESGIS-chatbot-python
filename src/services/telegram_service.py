"""
Service pour gérer les interactions du bot Telegram.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from ..db.db_adapter import DatabaseAdapter
from .mistral_client import MistralClient
from ..config.env import config

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TelegramService:
    """Service pour gérer les interactions du bot Telegram."""
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """
        Initialise le service Telegram.
        
        Args:
            db_adapter: Adaptateur de base de données à utiliser
        """
        self.token = config.TELEGRAM_BOT_TOKEN
        
        if not self.token:
            raise ValueError('TELEGRAM_BOT_TOKEN n\'est pas défini dans les variables d\'environnement')
        
        self.db_adapter = db_adapter
        self.mistral_client = MistralClient()
        self.chat_mode = {}  # Suivre quels chats sont en mode chat
        
        # Initialiser l'application Telegram
        self.app = Application.builder().token(self.token).build()
        
        # Configurer les gestionnaires de commandes et de messages
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configure les gestionnaires de commandes et de messages."""
        # Gestionnaires de commandes
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("chat", self._chat_command))
        self.app.add_handler(CommandHandler("reset", self._reset_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        
        # Gestionnaire de messages
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Gestionnaire de callbacks (pour les boutons)
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Gestionnaire d'erreurs
        self.app.add_error_handler(self._error_handler)
    
    async def start_polling(self):
        """Démarre le bot en mode polling."""
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("Le bot Telegram a démarré en mode polling")
    
    async def stop(self):
        """Arrête le bot avec gestion des erreurs."""
        try:
            # Arrêter l'updater avec un timeout pour éviter les blocages
            if self.app.updater:
                try:
                    # Utiliser asyncio.wait_for pour imposer un timeout
                    import asyncio
                    await asyncio.wait_for(self.app.updater.stop(), timeout=2.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout lors de l'arrêt de l'updater, continuation forcée")
                except asyncio.CancelledError:
                    logger.warning("Tâche d'arrêt de l'updater annulée, continuation forcée")
                except Exception as e:
                    logger.warning(f"Erreur lors de l'arrêt de l'updater: {str(e)}")
            
            # Arrêter l'application
            try:
                await asyncio.wait_for(self.app.stop(), timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError, Exception) as e:
                logger.warning(f"Erreur lors de l'arrêt de l'application: {str(e)}")
            
            # Arrêter l'application complètement
            try:
                await asyncio.wait_for(self.app.shutdown(), timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError, Exception) as e:
                logger.warning(f"Erreur lors de l'arrêt complet de l'application: {str(e)}")
                
            logger.info("Le bot Telegram a été arrêté")
            
        except Exception as e:
            logger.error(f"Erreur critique lors de l'arrêt du bot: {str(e)}")
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère la commande /start.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        chat_id = update.effective_chat.id
        username = update.effective_user.username or 'user'
        
        welcome_message = 'Bonjour ! Je suis votre assistant IA alimenté par Mistral AI. Comment puis-je vous aider aujourd\'hui?\n\n' \
                          'Utilisez /chat pour démarrer une conversation avec moi\n' \
                          'Utilisez /reset pour effacer notre historique de conversation\n' \
                          'Utilisez /help pour voir toutes les commandes disponibles'
        
        await update.message.reply_text(welcome_message)
    
    async def _chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère la commande /chat.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        chat_id = update.effective_chat.id
        username = update.effective_user.username or 'user'
        
        self.chat_mode[chat_id] = True
        
        await update.message.reply_text('Mode chat activé ! Vous pouvez maintenant me parler directement. Que voulez-vous discuter ?')
    
    async def _reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère la commande /reset.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        chat_id = update.effective_chat.id
        
        await self.db_adapter.reset_conversation(chat_id)
        
        await update.message.reply_text('Votre historique de conversation a été réinitialisé.')
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère la commande /help.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        chat_id = update.effective_chat.id
        
        help_message = 'Commandes disponibles:\n\n' \
                       '/start - Démarrer la conversation et afficher le menu\n' \
                       '/chat - Commencer à discuter avec l\'IA\n' \
                       '/reset - Réinitialiser votre historique de conversation\n' \
                       '/help - Afficher ce message d\'aide'
        
        await update.message.reply_text(help_message)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère les messages texte normaux.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        chat_id = update.effective_chat.id
        username = update.effective_user.username or 'user'
        message = update.message.text
        
        # Si le chat n'est pas en mode chat, activer automatiquement le mode chat
        if not self.chat_mode.get(chat_id):
            self.chat_mode[chat_id] = True
            logger.info(f"Mode chat automatiquement activé pour l'ID de chat: {chat_id}")
        
        # Indiquer que le bot est en train d'écrire
        await update.effective_chat.send_action(action="typing")
        
        # Traiter le message
        response = await self.process_message(chat_id, username, message)
        
        # Ajouter des boutons de feedback
        keyboard = [
            [
                InlineKeyboardButton("👍", callback_data="feedback_positive"),
                InlineKeyboardButton("👎", callback_data="feedback_negative")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Envoyer la réponse
        await update.message.reply_text(response, reply_markup=reply_markup)
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère les callbacks des boutons inline.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        query = update.callback_query
        await query.answer()
        
        if query.data == "feedback_positive":
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("Merci pour votre feedback positif ! 😊")
        elif query.data == "feedback_negative":
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("Je suis désolé que ma réponse n'ait pas été utile. Comment puis-je m'améliorer ?")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gère les erreurs survenues lors du traitement des mises à jour.
        
        Args:
            update: L'objet Update de Telegram
            context: Le contexte de la conversation
        """
        logger.error(f"Erreur lors du traitement de la mise à jour {update}: {context.error}")
    
    async def process_callback(self, callback_query: Dict[str, Any]) -> None:
        """
        Traite un callback de bouton inline.
        
        Args:
            callback_query: Données du callback
        """
        try:
            from telegram import Update
            from telegram.ext import CallbackContext, ContextTypes
            
            # Créer un objet Update factice pour le callback
            update = Update(0)
            update.callback_query = callback_query
            
            # Créer un contexte factice
            context = CallbackContext(update=update)
            
            # Traiter le callback
            await self._handle_callback(update, context)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du callback: {str(e)}")
    
    async def send_message(self, chat_id: int, text: str) -> None:
        """
        Envoie un message via l'API Telegram directement.
        
        Args:
            chat_id: ID du chat Telegram
            text: Texte du message à envoyer
        """
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors de l'envoi du message: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
    
    async def process_message(self, chat_id: int, username: str, message: str) -> str:
        """
        Traite un message de l'API.
        
        Args:
            chat_id: ID du chat Telegram
            username: Nom d'utilisateur
            message: Contenu du message
            
        Returns:
            La réponse du bot
        """
        try:
            logger.info(f"Traitement du message de {username} (chat_id: {chat_id}): {message}")
            
            # Enregistrer le message de l'utilisateur
            try:
                await self.db_adapter.save_message(chat_id, username, message)
                logger.info("Message utilisateur enregistré avec succès dans la base de données")
            except Exception as db_error:
                logger.error(f"Erreur lors de l'enregistrement du message: {str(db_error)}")
                logger.exception(db_error)
            
            # Obtenir le contexte de la conversation
            try:
                conversation = await self.db_adapter.get_conversation(chat_id, limit=5)
                logger.info(f"Contexte de la conversation récupéré: {len(conversation)} messages")
            except Exception as conv_error:
                logger.error(f"Erreur lors de la récupération de la conversation: {str(conv_error)}")
                logger.exception(conv_error)
                conversation = []
            
            # Obtenir une réponse du modèle Mistral
            try:
                logger.info("Appel à l'API Mistral...")
                # Convertir la conversation en format attendu par Mistral
                conversation_history = [
                    {"role": "user" if msg.get("from") == "user" else "assistant", "content": msg.get("content", "")}
                    for msg in conversation
                ]
                # Utiliser le dernier message comme prompt
                prompt = conversation[-1].get("content", "") if conversation else ""
                response = await self.mistral_client.get_completion(prompt, conversation_history[:-1])
                logger.info("Réponse reçue de l'API Mistral")
                
                # Enregistrer la réponse du bot
                try:
                    await self.db_adapter.save_message(chat_id, "assistant", response)
                    logger.info("Réponse du bot enregistrée avec succès")
                except Exception as save_error:
                    logger.error(f"Erreur lors de l'enregistrement de la réponse: {str(save_error)}")
                    logger.exception(save_error)
                
                return response
                
            except Exception as mistral_error:
                logger.error(f"Erreur lors de l'appel à l'API Mistral: {str(mistral_error)}")
                logger.exception(mistral_error)
                return "Désolé, une erreur est survenue lors de la génération de la réponse. Veuillez réessayer plus tard."
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors du traitement du message: {str(e)}")
            logger.exception(e)
            return "Désolé, une erreur inattendue est survenue. Veuillez réessayer plus tard."
