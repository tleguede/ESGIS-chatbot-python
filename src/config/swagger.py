"""
Configuration Swagger pour l'API FastAPI.
"""
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi


def setup_swagger(app: FastAPI) -> None:
    """
    Configure Swagger pour l'API FastAPI.
    
    Args:
        app: Application FastAPI à configurer
    """
    # Personnaliser les métadonnées OpenAPI
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="ESGIS Telegram Chatbot API",
            version="1.0.0",
            description="API pour le chatbot Telegram intégré avec Mistral AI",
            routes=app.routes,
            openapi_version="3.0.2"
        )
        
        # Personnaliser les tags
        openapi_schema["tags"] = [
            {
                "name": "chat",
                "description": "Opérations liées au chat",
            },
            {
                "name": "health",
                "description": "Vérifications de l'état de santé",
            }
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Personnaliser la page Swagger UI
    @app.get("/", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Documentation API",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        )
