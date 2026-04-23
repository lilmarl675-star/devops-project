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
                    sleep 15
                    
                    echo "Vérification de l'application Flask..."
                    curl -f http://localhost:5000/ || exit 1
                    
                    echo "Vérification de Prometheus..."
                    curl -f http://localhost:9090/ || exit 1
                    
                    echo "Attente que Grafana soit prêt..."
                    for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
                        echo "Tentative $i/15..."
                        if curl -s -f http://localhost:3000/ > /dev/null 2>&1; then
                            echo "✅ Grafana est prêt !"
                            exit 0
                        fi
                        echo "Grafana pas encore prêt, attente 5 secondes..."
                        sleep 5
                    done
                    echo "❌ Grafana n'a pas démarré après 75 secondes"
                    exit 1
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
