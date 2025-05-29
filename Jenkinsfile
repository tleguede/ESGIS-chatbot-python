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
                
                // Vérifier les versions de Python disponibles
                sh '''
                    echo "Python3 path: $(which python3)"
                    python3 --version
                '''
                
                // Modifier le Makefile pour utiliser python3 au lieu de python
                sh '''
                    sed -i 's/python -m venv venv/python3 -m venv venv/g' Makefile
                    sed -i 's/python -m src/python3 -m src/g' Makefile
                '''
                
                // Exécuter make venv et make install
                sh "make venv && make install"
            }
        }

        stage('Environment variable injection'){
            steps {
                script{
                    // Copier le fichier .env.example vers .env
                    sh "cp .env.example .env"
                    
                    // Injecter les credentials dans le fichier .env
                    withCredentials([
                        string(credentialsId: 'telegram-bot-token', variable: 'TELEGRAM_TOKEN'),
                        string(credentialsId: 'mistral-api-key', variable: 'MISTRAL_KEY')
                    ]) {
                        sh '''
                            sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${TELEGRAM_TOKEN}|g" .env
                            sed -i "s|MISTRAL_API_KEY=.*|MISTRAL_API_KEY=${MISTRAL_KEY}|g" .env
                        '''
                    }
                    
                    // Afficher un message de confirmation
                    sh "echo 'Environment variables injected successfully'"
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
                    sh "make deploy env=${BRANCH_NAME}"
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