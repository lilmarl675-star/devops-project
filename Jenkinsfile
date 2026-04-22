pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Docker') {
            steps {
                sh 'docker build -t flask-app ./app'
            }
        }
        
        stage('Clean old containers') {
            steps {
                sh 'docker compose down --remove-orphans || true'
                sh 'docker rm -f flask-app prometheus grafana 2>/dev/null || true'
            }
        }
        
        stage('Compose Up') {
            steps {
                sh 'docker compose up -d'
            }
        }
        
        stage('Verify') {
            steps {
                sh '''
                    echo "Attente du démarrage des services..."
                    sleep 10
                    
                    echo "Vérification de l'application Flask..."
                    curl -f http://localhost:5000/ || exit 1
                    
                    echo "Vérification de Prometheus..."
                    curl -f http://localhost:9090/ || exit 1
                    
                    echo "Attente supplémentaire pour Grafana..."
                    sleep 10
                    
                    echo "Vérification de Grafana..."
                    curl -f http://localhost:3000/ || exit 1
                    
                    echo "Tous les services sont opérationnels !"
                '''
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline réussi !'
        }
        failure {
            echo '❌ Pipeline échoué !'
        }
    }
}
