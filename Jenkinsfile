pipeline {
    agent {
        label 'master'
    }
    stages {
        stage('Test') {
            agent {
                docker {
                    image 'python:3.7'
                    reuseNode true
                    args '-v /tmp/.pipcache:/root/.cache'
                }
            }
            steps {
                sh "test.sh"
            }
        }
    }
}
