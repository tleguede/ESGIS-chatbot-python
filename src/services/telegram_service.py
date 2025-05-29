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
        """Arrête le bot."""
        if self.app.updater:
            await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Le bot Telegram a été arrêté")
    
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
        # Sauvegarder le message de l'utilisateur
        await self.db_adapter.save_message(chat_id, username, message)
        
        # Récupérer l'historique de conversation
        conversation_history = await self.db_adapter.get_conversation(chat_id)
        
        # Obtenir une réponse de Mistral AI
        response = await self.mistral_client.get_completion(message, conversation_history)
        
        # Sauvegarder la réponse du bot
        await self.db_adapter.save_response(chat_id, response)
        
        return response
