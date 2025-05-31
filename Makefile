.PHONY: bot clean venv install build deploy-local deploy serve test test-endpoint webhook-status webhook-delete webhook-setup webhook-setup-win

bot:
	python -m src.telegram_bot

# by default, we settle down in this region
AWS_REGION ?= eu-west-3
AWS_PROFILE ?= "esgis_profile"

clean:
	rm -rf venv
	rm -rf __pycache__
	rm -rf *.egg-info
	rm -rf .pytest_cache

venv: clean
	python3 -m venv venv

install:
	venv/bin/pip install -r requirements-lambda.txt
	venv/bin/pip install -r requirements.txt

build:
	sam build --use-container -t infrastructure/template.yaml

deploy-local:
	sam local start-api

deploy:
	@echo "Deploying to " ${env}
	# Optimiser le package Lambda
	@echo "Optimizing Lambda package..."
	# Copier requirements-lambda.txt vers requirements.txt pour réduire la taille du package
	cp requirements-lambda.txt requirements.txt
	
	# S'assurer que mangum est installé dans l'environnement virtuel
	@echo "Installing mangum in virtual environment..."
	. venv/bin/activate && pip install mangum
	
	# Build avec SAM
	@echo "Building with SAM..."
	sam build --use-container --template-file infrastructure/template.yaml \
		--parameter-overrides "EnvironmentName=${env}"
	
	# Vérifier que mangum est bien dans le package
	@echo "Checking if mangum is in the package..."
	ls -la .aws-sam/build/Function/
	
	# Installer manuellement les dépendances dans le package
	@echo "Installing dependencies in the package..."
	pip install -r requirements.txt -t .aws-sam/build/Function/
	
	# Déployer avec SAM
	@echo "Deploying with SAM..."
	sam deploy --resolve-s3 --stack-name multi-stack-${env} \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --region ${AWS_REGION} \
		--parameter-overrides "EnvironmentName=${env} TelegramBotToken=${TELEGRAM_BOT_TOKEN} MistralApiKey=${MISTRAL_API_KEY}" \
		--no-fail-on-empty-changeset

serve:
	venv/bin/fastapi dev src/main.py

test:
	@echo "Running tests..."
	# venv/bin/pytest

test-endpoint:
	@echo "Running endpoint tests..."
	aws cloudformation describe-stacks --stack-name multi-stack-${env} --region ${AWS_REGION} \
		--query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text | xargs -I {} curl -X GET {}