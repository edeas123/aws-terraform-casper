pipeline {
  agent {
    docker {
      image 'python:3.7.4-stretch'
    }

  }
  stages {
    stage('install dependencies') {
      steps {
        sh 'python3 -m venv venv'
        sh 'source venv/bin/activate'
        sh 'pip install -r requirements.txt'
      }
    }

    stage('Install Test Dependencies') {
      steps {
        sh 'pip install pytest pytest-cov codecov'
      }
    }

    stage('Test') {
      steps {
        sh 'PYTHONPATH=. pytest --cov=./casper'
        sh 'codecov'
      }
    }

  }
}