pipeline {
    agent any

    options {
        ansiColor('xterm')
    }

    environment {
        // Define environment variables here
        BOT_NAME = 'awesome-bot'
        // BOT_TOKEN = credentials('telegram-bot-token')
    }

    stages {

        stage('Initialisation') {
            steps {
                sh "echo Branch name ${BRANCH_NAME}"
                
                // Vérifier l'installation de Python
                sh '''
                    echo "Vérification de l'environnement Python..."
                    which python3 || which python || echo "Python n'est pas installé ou n'est pas dans le PATH"
                    python3 --version || python --version || echo "Impossible d'obtenir la version de Python"
                '''
                
                // Créer l'environnement virtuel et installer les dépendances
                sh "make venv && make install"
            }
        }

        stage('Environment variable injection'){
            steps {
                script {
                    echo "Setting up environment variables..."
                    
                    // Copier le fichier .env.example vers .env
                    sh "cp .env.example .env"
                    
                    // Si le credential existe, l'utiliser, sinon continuer avec les valeurs par défaut
                    try {
                        withCredentials([file(credentialsId: 'tleguede-chatbot-env-file', variable: 'ENV_FILE')]) {
                            sh "cat $ENV_FILE > .env"
                            echo "Using credentials from tleguede-chatbot-env-file"
                        }
                    } catch (Exception e) {
                        echo "Warning: tleguede-chatbot-env-file not found, using .env.example values"
                    }
                    
                    // Afficher les premières lignes du fichier .env pour le débogage (sans afficher les valeurs sensibles)
                    sh '''
                        echo "Current .env file content (first 5 lines):"
                        head -n 5 .env || true
                        echo "..."
                    '''
                }
            }
        }

        stage('Tests Unitaires') {
            steps {
                script {
                    // Add your test commands here
                    echo "Running tests..."
                    sh "make test"
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    // Add your build commands here
                    echo "Building the project..."
                    sh "make build"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    // Add your deployment commands here
                    echo "Deploying the project..."
                    
                    // Read the .env file to get the values
                    def envVars = readFile('.env')
                    def telegramToken = (envVars =~ /TELEGRAM_BOT_TOKEN=["']?([^\r\n"']+)["']?/)[0][1]
                    def mistralKey = (envVars =~ /MISTRAL_API_KEY=["']?([^\r\n"']+)["']?/)[0][1]
                    def api_url = (envVars =~ /API_URL=["']?([^\r\n"']+)["']?/)[0][1]
                    
                    // Deploy with the environment variables
                    sh "make deploy env=${BRANCH_NAME} TELEGRAM_BOT_TOKEN='${telegramToken}' MISTRAL_API_KEY='${mistralKey}' API_URL='${api_url}'"
                }
            }
        }

        stage('Test endpoint'){
            steps {
                script {
                    // Add your endpoint testing commands here
                    echo "Testing the endpoint..."
                    sh "make test-endpoint env=${BRANCH_NAME}"
                }
            }
        }
    }

    post {
        always {
            script {
                // Add your post-build actions here
                echo "Post-build actions..."
            }
        }
        success {
            script {
                // Notify success
                echo "Build succeeded!"
                // Uncomment the line below to send a message to Telegram
                // sh "curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/sendMessage -d chat_id=<CHAT_ID> -d text='Build succeeded!'"
            }
        }
        failure {
            script {
                // Notify failure
                echo "Build failed!"
                // Uncomment the line below to send a message to Telegram
                // sh "curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/sendMessage -d chat_id=<CHAT_ID> -d text='Build failed!'"
            }
        }
    }

}