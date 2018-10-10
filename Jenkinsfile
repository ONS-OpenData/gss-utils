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
                }
            }
            steps {
                sh "make test"
            }
        }
    }
}
