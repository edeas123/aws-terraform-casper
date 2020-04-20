pipeline {
  agent {
    docker {
      image 'python:3.7.4-stretch'
    }

  }
  stages {
    stage('install dependencies') {
      steps {
        sh 'pip install -r requirements.txt'
      }
    }

  }
}