"""
Interface en ligne de commande pour la gestion des webhooks Telegram.
"""
import argparse
import asyncio
import logging
import sys
from typing import Optional

from .webhook_utils import delete_webhook, get_webhook_info, setup_webhook
from ..config.env import config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def check_webhook_status(token: Optional[str] = None) -> None:
    """Affiche les informations sur le webhook actuel."""
    print("\n🔍 Récupération des informations du webhook...")
    webhook_info = get_webhook_info(token)
    
    if not webhook_info:
        print("❌ Impossible de récupérer les informations du webhook")
        return
    
    result = webhook_info.get('result', {})
    
    if not result.get('url'):
        print("ℹ️ Aucun webhook actif détecté.")
        return
    
    print("\nℹ️ Webhook actuel:")
    print(f"URL: {result['url']}")
    print(f"A un certificat personnalisé: {result.get('has_custom_certificate', False)}")
    print(f"Nombre de mises à jour en attente: {result.get('pending_update_count', 0)}")
    
    if 'last_error_date' in result:
        from datetime import datetime
        error_date = datetime.fromtimestamp(result['last_error_date']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Dernière erreur ({error_date}): {result.get('last_error_message', 'Aucun détail')}")
    else:
        print("Dernière erreur: Jamais")

async def main() -> None:
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description='Gestion des webhooks Telegram')
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # Commande: status
    subparsers.add_parser('status', help='Afficher le statut du webhook')
    
    # Commande: delete
    delete_parser = subparsers.add_parser('delete', help='Supprimer le webhook existant')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Supprimer sans confirmation')
    
    # Commande: setup
    setup_parser = subparsers.add_parser('setup', help='Configurer un nouveau webhook')
    setup_parser.add_argument('--url', help='URL de base pour le webhook (par défaut: API_URL de la config)')
    
    # Afficher l'aide si aucune commande n'est fournie
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Vérifier que le token est configuré
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ ERREUR: La variable d'environnement TELEGRAM_BOT_TOKEN n'est pas définie")
        sys.exit(1)
    
    # Exécuter la commande demandée
    if args.command == 'status':
        await check_webhook_status(config.TELEGRAM_BOT_TOKEN)
    
    elif args.command == 'delete':
        if not args.force:
            confirm = input("Êtes-vous sûr de vouloir supprimer le webhook actuel ? (o/N) ")
            if confirm.lower() != 'o':
                print("Opération annulée.")
                return
        
        success, message = await delete_webhook(config.TELEGRAM_BOT_TOKEN)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    elif args.command == 'setup':
        base_url = args.url or config.API_URL
        if not base_url:
            print("❌ ERREUR: Aucune URL de base fournie et API_URL n'est pas défini dans la configuration")
            sys.exit(1)
        
        print(f"Configuration du webhook vers: {base_url}/api/chat/update")
        success, message = await setup_webhook(config.TELEGRAM_BOT_TOKEN, base_url)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")

if __name__ == "__main__":
    asyncio.run(main())
