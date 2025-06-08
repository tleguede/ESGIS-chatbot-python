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

        stage('Delete Stuck Stack') {
            steps {
                script {
                    def stackName = "multi-stack-${env.BRANCH_NAME}"
                    echo "Suppression du stack bloqué CloudFormation (${stackName}) si besoin..."
                    sh """
                        aws cloudformation delete-stack --stack-name \${stackName} --region eu-west-3 || true
                        echo "Attente de la suppression du stack..."
                        for i in \\$(seq 1 30); do
                            status=\\$(aws cloudformation describe-stacks --stack-name \${stackName} --region eu-west-3 --query \"Stacks[0].StackStatus\" --output text 2>&1)
                            if [ \${?} -ne 0 ]; then
                                echo \"Stack supprimé ou inexistant.\"
                                break
                            fi
                            echo \"\${status}\" | grep -q \"ValidationError\"
                            if [ \${?} -eq 0 ] || [ \"\${status}\" = \"DELETE_COMPLETE\" ]; then
                                echo \"Stack supprimé ou inexistant.\"
                                break
                            fi
                            echo \"Statut actuel: \${status}, attente...\"
                            sleep 10
                        done
                    """
                }
            }
        }

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
                            python ./set_webhook.py --url "${apiUrl}/api/chat/update"
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