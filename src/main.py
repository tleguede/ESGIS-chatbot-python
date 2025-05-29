"""
Point d'entrée principal pour démarrer le serveur.
"""
import logging
import uvicorn
import sys
from .config.env import config, validate_env
from .app import create_app

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Fonction principale pour démarrer le serveur."""
    # Vérifier que les variables d'environnement requises sont définies
    missing_vars = validate_env()
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes : {', '.join(missing_vars)}")
        logger.error("Veuillez définir ces variables dans le fichier .env")
        sys.exit(1)
    
    # Créer l'application
    app = create_app()
    
    # Démarrer le serveur
    logger.info(f"Démarrage du serveur sur le port {config.PORT}")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.ENV == "development"
    )


# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    main()


# Créer une instance de l'application pour uvicorn
app = create_app()
