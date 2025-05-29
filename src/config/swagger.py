"""
Configuration Swagger pour l'API FastAPI avec gestion robuste des erreurs.
"""
import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


def get_minimal_openapi() -> Dict[str, Any]:
    """Retourne une configuration OpenAPI minimale en cas d'erreur."""
    return {
        "openapi": "3.0.2",
        "info": {
            "title": "ESGIS Telegram Chatbot API",
            "version": "1.0.0",
            "description": "Documentation de l'API (version minimale en raison d'une erreur de génération)"
        },
        "paths": {
            "/api/chat/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "Health Check",
                    "responses": {
                        "200": {
                            "description": "Service opérationnel",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "version": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {"name": "chat", "description": "Endpoints pour l'interaction avec le chatbot"},
            {"name": "health", "description": "Vérification de l'état du service"}
        ]
    }


def setup_swagger(app: FastAPI) -> None:
    """
    Configure Swagger pour l'API FastAPI avec une meilleure gestion des erreurs.
    
    Args:
        app: Application FastAPI à configurer
    """
    # Middleware pour gérer les erreurs OpenAPI
    @app.middleware("http")
    async def handle_openapi_errors(request: Request, call_next):
        try:
            if request.url.path in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]:
                try:
                    return await call_next(request)
                except Exception as e:
                    if request.url.path == "/openapi.json":
                        return JSONResponse(content=get_minimal_openapi())
                    return JSONResponse(
                        status_code=500,
                        content={"detail": f"Erreur lors de la génération de la documentation: {str(e)}"}
                    )
            return await call_next(request)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Erreur interne du serveur: {str(e)}"}
            )
    
    # Personnaliser les métadonnées OpenAPI avec gestion des erreurs
    def custom_openapi() -> Dict[str, Any]:
        if hasattr(app, "openapi_schema") and app.openapi_schema:
            return app.openapi_schema
            
        try:
            # Obtenir le schéma OpenAPI de base
            openapi_schema = get_openapi(
                title="ESGIS Telegram Chatbot API",
                version="1.0.0",
                description="API pour le chatbot Telegram intégré avec Mistral AI",
                routes=app.routes if hasattr(app, 'routes') else [],
                openapi_version="3.0.2"
            )
            
            # Personnaliser les tags
            openapi_schema["tags"] = [
                {
                    "name": "chat",
                    "description": "Endpoints pour l'interaction avec le chatbot"
                },
                {
                    "name": "health",
                    "description": "Vérification de l'état du service"
                },
                {
                    "name": "webhook",
                    "description": "Gestion des webhooks Telegram"
                }
            ]
            
            # S'assurer que les composants existent
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            
            if "schemas" not in openapi_schema["components"]:
                openapi_schema["components"]["schemas"] = {}
            
            # Exemple de schéma pour les messages
            openapi_schema["components"]["schemas"]["Message"] = {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Bonjour, comment puis-je vous aider ?"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2023-01-01T12:00:00Z"
                    }
                }
            }
            
            app.openapi_schema = openapi_schema
            return app.openapi_schema
            
        except Exception as e:
            # En cas d'erreur, retourner un schéma minimal
            return get_minimal_openapi()
    
    # Configurer l'interface utilisateur Swagger
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        try:
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title="ESGIS Chatbot API - Documentation",
                oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url if hasattr(app, 'swagger_ui_oauth2_redirect_url') else None,
                swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
            )
        except Exception as e:
            return HTMLResponse("""
                <html>
                    <head>
                        <title>Documentation API - Erreur</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 40px; }
                            .error { color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 5px; }
                        </style>
                    </head>
                    <body>
                        <h1>Documentation de l'API</h1>
                        <div class="error">
                            <h2>Erreur lors du chargement de la documentation</h2>
                            <p>La documentation n'a pas pu être chargée en raison d'une erreur interne.</p>
                            <p>Veuillez réessayer ou consulter les logs du serveur pour plus d'informations.</p>
                        </div>
                        <p><a href="/api/chat/health">Vérifier l'état du service</a></p>
                    </body>
                </html>
            """)
    
    # Appliquer la configuration personnalisée
    try:
        app.openapi = custom_openapi
    except Exception as e:
        # En cas d'erreur, utiliser une configuration minimale
        app.openapi = get_minimal_openapi
