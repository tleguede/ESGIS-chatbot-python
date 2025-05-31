FROM amazon/aws-lambda-python:3.11

# Installer AWS SAM CLI et autres outils
RUN yum update -y && \
    yum install -y gcc python3-devel tar gzip unzip && \
    pip install --no-cache-dir aws-sam-cli

WORKDIR /var/task

# Copier les fichiers de dépendances
COPY requirements.txt requirements-lambda.txt ./

# Installer les dépendances (utiliser requirements-lambda.txt pour l'environnement Lambda)
RUN pip install --no-cache-dir -r requirements-lambda.txt

# Copier le reste du code source
COPY . .

# Exposer le port sur lequel l'application s'exécute
EXPOSE 3000

# Définir les variables d'environnement pour simuler AWS Lambda
ENV PORT=3000
ENV NODE_ENV=production
ENV IS_LAMBDA_ENVIRONMENT=true
ENV USE_MEMORY_ADAPTER=true
ENV AWS_LAMBDA_FUNCTION_NAME=esgis-chatbot
ENV AWS_LAMBDA_FUNCTION_VERSION=1.0.0
ENV AWS_REGION=eu-west-3
ENV AWS_EXECUTION_ENV=AWS_Lambda_python3.11

# Créer un script d'entrée pour simuler l'environnement Lambda
RUN echo '#!/bin/bash\n\
# Démarrer le serveur FastAPI\n\
python -m uvicorn src.app:app --host 0.0.0.0 --port 3000' > /var/task/entrypoint.sh && \
    chmod +x /var/task/entrypoint.sh

# Commande pour démarrer l'application
CMD ["/var/task/entrypoint.sh"]
