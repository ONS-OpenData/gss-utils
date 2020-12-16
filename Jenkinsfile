pipeline {
    agent {
        label 'master'
    }
    stages {
        stage('Test') {
            agent {
                docker {
                    image 'python:3.9'
                    reuseNode true
                    alwaysPull true
                    args '-u root:root -v /tmp/.pipcache:/root/.cache'
                }
            }
            steps {
                sh "./test.sh"
            }
        }
    }
    post {
        always {
            cucumber 'test-results.json'
        }
    }
}
