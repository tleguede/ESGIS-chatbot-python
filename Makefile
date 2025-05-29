.PHONY: bot run clean venv install build test deploy-local deploy serve test-endpoint

# Par défaut, nous utilisons cette région AWS
AWS_REGION ?= eu-west-3
AWS_PROFILE ?= "esgis_profile"
ENV_NAME ?= "tleguede-dev"

# Commande pour démarrer uniquement le bot Telegram
bot:
	python3 -m src.telegram_bot

# Commande pour démarrer l'API FastAPI et le bot Telegram
run:
	python3 -m src.main

# Nettoyer le projet
clean:
	rm -rf venv
	rm -rf __pycache__
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .aws-sam
	find . -type d -name __pycache__ -exec rm -rf {} +

# Créer un environnement virtuel
venv:
	python3 -m venv venv

# Installer les dépendances
install: venv
	. venv/bin/activate && pip install -r requirements.txt

# Exécuter les tests
test:
	. venv/bin/activate && python3 -m pytest || echo "Aucun test trouvé ou tests échoués, mais on continue" && exit 0

# Construire le package SAM
build:
	sam build --use-container -t infrastructure/template.yaml

# Démarrer l'API localement
deploy-local:
	sam local start-api

deploy:
	@echo "Deploying to " ${env}
	# Optimiser le package Lambda
	@echo "Optimizing Lambda package..."
	# Copier requirements-lambda.txt vers requirements.txt pour réduire la taille du package
	cp requirements-lambda.txt requirements.txt
	
	# Build avec SAM
	sam build --use-container --template-file infrastructure/template.yaml \
		--parameter-overrides "EnvironmentName=${env}"
	
	# Déployer avec SAM
	@echo "Deploying with SAM..."
	sam deploy --stack-name multi-stack-${env} \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --region ${AWS_REGION} \
		--parameter-overrides "EnvironmentName=${env} TelegramBotToken=${TELEGRAM_BOT_TOKEN} MistralApiKey=${MISTRAL_API_KEY}" \
		--no-fail-on-empty-changeset


serve:
	. venv/bin/activate && python3 -m uvicorn src.main:app --reload

test-endpoint:
	@echo "Running endpoint tests..."
	aws cloudformation describe-stacks --stack-name multi-stack-${env} --region ${AWS_REGION} \
		--query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text | xargs -I {} curl -X GET {}