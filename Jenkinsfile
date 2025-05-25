pipeline {
    agent any

    environment {
        IMAGE_NAME = "digiapi-backend"
        CONTAINER_NAME = "digiapi-container"
        PORT = "9000"
    }

    stages {
        stage('Clone Repo') {
            steps {
                git branch: 'Dockerized-FastAPI', url: 'https://github.com/Hari-Charan-00/DigitalWallet.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt pytest'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest test_main.py'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME .'
            }
        }

        stage('Stop Existing Container') {
            steps {
                sh 'docker rm -f $CONTAINER_NAME || true'
            }
        }

        stage('Run Docker Container') {
            steps {
                sh 'docker run -d -p $PORT:$PORT --name $CONTAINER_NAME $IMAGE_NAME'
            }
        }
    }
}

