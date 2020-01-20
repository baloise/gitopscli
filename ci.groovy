pipeline {
    agent any
    environment {
        hash = ''
        image = ''
    }
    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/baloise-incubator/gitopscli.git',
                        credentialsId: '0f34a51f-334f-4ebe-a663-90e312fb32f6'
                script {
                    hash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }
        stage('Build & Push') {
            steps {
                withCredentials([[$class          : 'UsernamePasswordMultiBinding', credentialsId: 'e27f88c4-b4da-4dea-875b-8d763aac9949',
                                  usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                    script {
                        image = "docker.io/baloiseincubator/gitopscli:${hash}"
                    }
                    sh 'sudo podman login docker.io -u $USERNAME -p $PASSWORD'
                    sh "sudo podman build . -t ${image}"
                    sh "sudo podman push ${image}"
                }
            }
        }
    }
}