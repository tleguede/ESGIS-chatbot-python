.PHONY: bot run clean venv install build test deploy-local deploy serve test-endpoint

# Par défaut, nous utilisons cette région AWS
AWS_REGION ?= eu-west-3
AWS_PROFILE ?= "esgis_profile"
ENV_NAME ?= "tleguede-dev"

# Commande pour démarrer uniquement le bot Telegram
bot:
	python -m src.telegram_bot

# Commande pour démarrer l'API FastAPI et le bot Telegram
run:
	python -m src.main

# Nettoyer le projet
clean:
	if exist "venv" rd /s /q venv
	if exist "__pycache__" rd /s /q __pycache__
	if exist "*.egg-info" rd /s /q *.egg-info
	if exist ".pytest_cache" rd /s /q .pytest_cache
	if exist ".aws-sam" rd /s /q .aws-sam
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

# Créer un environnement virtuel
venv:
	python -m venv venv

# Installer les dépendances
install: venv
	venv\Scripts\pip install -r requirements.txt

# Exécuter les tests
test:
	venv\Scripts\pytest

# Construire le package SAM
build:
	sam build --use-container -t infrastructure/template.yaml

# Démarrer l'API localement
deploy-local:
	sam local start-api

deploy:
	@echo "Deploying to " ${env}
	# Extract env from the branch name

	sam deploy --resolve-s3 --template-file .aws-sam/build/template.yaml --stack-name multi-stack-${env} \
         --capabilities CAPABILITY_IAM --region ${AWS_REGION} --parameter-overrides EnvironmentName=${env} --no-fail-on-empty-changeset


serve:
	venv\Scripts\python -m uvicorn src.main:app --reload

test-endpoint:
	@echo "Running endpoint tests..."
	aws cloudformation describe-stacks --stack-name multi-stack-${env} --region ${AWS_REGION} \
		--query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text | xargs -I {} curl -X GET {}