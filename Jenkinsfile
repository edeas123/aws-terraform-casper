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
        sh '. venv/bin/activate'
        sh 'pip3 install -r requirements.txt'
      }
    }

    stage('Install Test Dependencies') {
      steps {
        sh 'pip3 install pytest pytest-cov codecov'
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