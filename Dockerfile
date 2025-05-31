FROM python:3.11-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Exposer le port sur lequel l'application s'exécute
EXPOSE 3000

# Définir les variables d'environnement
ENV PORT=3000
ENV NODE_ENV=production
ENV IS_LAMBDA_ENVIRONMENT=false
ENV USE_MEMORY_ADAPTER=true

# Commande pour démarrer l'application
CMD ["python", "-m", "src.app"]
