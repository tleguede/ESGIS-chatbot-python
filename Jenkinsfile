pipeline {
    agent any

    options {
        ansiColor('xterm')
        skipDefaultCheckout()
    }

    environment {
        BOT_NAME = 'awesome-bot'
        TELEGRAM_BOT_TOKEN = credentials('tleguede-telegram-bot-token')
        MISTRAL_API_KEY = credentials('tleguede-mistral-api-key')
        PYTHON_VERSION = '3.12'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Initialisation') {
            steps {
                script {
                    sh "echo Branch name: ${env.BRANCH_NAME}"
                    sh "make venv && make install"
                }
            }
        }

        stage('Environnement variable injection') {
            steps {
                withCredentials([file(credentialsId: 'tleguede-chatbot-env-file', variable: 'ENV_FILE')]) {
                    script {
                        sh "cat ${ENV_FILE} > .env"
                    }
                }
            }
        }

        // stage('Install SAM CLI') {
        //     steps {
        //         sh '''
        //             export HOME=/tmp
        //             mkdir -p $HOME/.local
        //             pip install --user aws-sam-cli
        //             $HOME/.local/bin/sam --version || sam --version
        //         '''
        //     }
        // }

        stage('Build') {
            steps {
                script {
                    echo "Building the project..."
                    sh 'make build'
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([
                    string(credentialsId: 'tleguede-telegram-bot-token', variable: 'TELEGRAM_BOT_TOKEN'),
                    string(credentialsId: 'tleguede-mistral-api-key', variable: 'MISTRAL_API_KEY')
                ]) {
                    script {
                        sh """
                            make deploy env=${env.BRANCH_NAME} \
                            TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN} \
                            MISTRAL_API_KEY=${MISTRAL_API_KEY}
                        """
                    }
                }
            }
        }

        stage('Configure Webhook') {
            steps {
                script {
                    // Get the API URL from CloudFormation outputs
                    def apiUrl = sh(
                        script: """
                            aws cloudformation describe-stacks \
                            --stack-name multi-stack-${env.BRANCH_NAME} \
                            --region eu-west-3 \
                            --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
                            --output text
                        """,
                        returnStdout: true
                    ).trim()

                    // Configure the webhook
                    withCredentials([string(credentialsId: 'tleguede-telegram-bot-token', variable: 'TELEGRAM_BOT_TOKEN')]) {
                        sh """
                            # Activate virtual environment and run the script
                            . .venv/bin/activate
                            python tools/set_webhook.py --url "${apiUrl}/telegram/webhook"
                            deactivate
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Build succeeded!"
        }
        failure {
            echo "Build failed!"
        }
    }
}