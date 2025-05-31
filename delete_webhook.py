"""
Script pour supprimer le webhook Telegram.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer le token du bot depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    print("ERREUR: La variable d'environnement TELEGRAM_BOT_TOKEN n'est pas définie")
    sys.exit(1)

def delete_webhook():
    """Supprime le webhook Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    
    print(f"Suppression du webhook...")
    try:
        response = requests.post(url, timeout=10)
        response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
        
        result = response.json()
        if result.get('ok') and result.get('result'):
            print("✅ Webhook supprimé avec succès!")
            print(f"Résultat: {result['description']}")
            return True
        else:
            print(f"❌ Échec de la suppression du webhook: {result.get('description', 'Raison inconnue')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def get_webhook_info():
    """Récupère les informations sur le webhook actuel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des informations du webhook: {e}")
        return None

if __name__ == "__main__":
    # Afficher les informations actuelles du webhook
    print("Récupération des informations du webhook actuel...")
    webhook_info = get_webhook_info()
    
    if webhook_info and webhook_info.get('ok'):
        result = webhook_info.get('result', {})
        if result.get('url'):
            print(f"\nℹ️ Webhook actuel:")
            print(f"URL: {result['url']}")
            print(f"A des certificat personnalisé: {result.get('has_custom_certificate', False)}")
            print(f"Nombre mises à jour en attente: {result.get('pending_update_count', 0)}")
            print(f"Dernière erreur: {result.get('last_error_message', 'Aucune erreur')}")
            print(f"Dernière date d'erreur: {result.get('last_error_date', 'Jamais')}")
        else:
            print("ℹ️ Aucun webhook actif détecté.")
    
    # Demander confirmation avant de supprimer le webhook
    if webhook_info and webhook_info.get('result', {}).get('url'):
        print("\nVoulez-vous supprimer le webhook actuel ? (o/n)")
        if input().strip().lower() == 'o':
            delete_webhook()
        else:
            print("Opération annulée.")
    else:
        print("\nAucun webhook actif à supprimer.")
