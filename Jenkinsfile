pipeline {
    agent any

    environment {
        APP_NAME = 'digiapi-container'
        IMAGE_NAME = 'digiapi-backend'
        PORT = '9000'
    }

    stages {

        stage('Clone Repo') {
            steps {
                git branch: 'Dockerized-FastAPI', url: 'https://github.com/Hari-Charan-00/DigitalWallet.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $IMAGE_NAME .
                '''
            }
        }

        stage('Stop Existing Container') {
            steps {
                sh '''
                    docker stop $APP_NAME || true
                    docker rm $APP_NAME || true
                '''
            }
        }

        stage('Run Docker Container') {
            steps {
                sh '''
                    docker run -d --name $APP_NAME -p $PORT:$PORT $IMAGE_NAME
                '''
            }
        }
    }

    post {
        always {
            echo "Cleaning up..."
            sh 'rm -rf venv'
        }
        failure {
            echo 'Build failed!'
        }
        success {
            echo 'Build succeeded!'
        }
    }
}
