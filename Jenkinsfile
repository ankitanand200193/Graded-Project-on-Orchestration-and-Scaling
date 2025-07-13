pipeline {
  agent any

  environment {
    AWS_ACCOUNT_ID = '975050024946'
    AWS_REGION = 'ap-south-1'
    IMAGE_TAG = 'latest'
  }

  triggers {
    githubPush()
  }

  options {
    skipDefaultCheckout()
  }

  stages {
    stage('Checkout Code') {
      when {
        branch 'main'
      }
      steps {
        git branch: 'main', url: 'https://github.com/ankitanand200193/Graded-Project-on-Orchestration-and-Scaling.git'
      }
    }

    stage('Login to Amazon ECR') {
      when {
        branch 'main'
      }
      steps {
        script {
          sh '''
          aws ecr get-login-password --region ${AWS_REGION} | \
          docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
          '''
        }
      }
    }

    stage('Build and Push backendprofileservice') {
      when {
        branch 'main'
      }
      steps {
        script {
          def image1 = docker.build("${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ankitanand/backendprofileservice:${IMAGE_TAG}", "./backend/backendprofileservice")
          image1.push()
        }
      }
    }

    stage('Build and Push backendhelloservice') {
      when {
        branch 'main'
      }
      steps {
        script {
          def image2 = docker.build("${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ankitanand/backendhelloservice:${IMAGE_TAG}", "./backend/backendhelloservice")
          image2.push()
        }
      }
    }

    stage('Build and Push frontend') {
      when {
        branch 'main'
      }
      steps {
        script {
          def image3 = docker.build("${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/ankitanand/frontend:${IMAGE_TAG}", "./frontend")
          image3.push()
        }
      }
    }
  }
}
