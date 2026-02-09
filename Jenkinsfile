pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = 'us-east-1' 
        STACKNAME = "Emails-RAG-Service-${ENV}"
        LambdaFunctionName = "Emails-RAG-Service-${ENV}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('SAM Build') {
            steps {
                sh 'sam build'
            }
        }
        stage('SAM Deploy') {
            steps {
                withAWS(roleAccount: env.AWS_ACCOUNT_ID, role: env.IAM_ROLE_NAME) {
                sh '''
                sam deploy --s3-bucket ${S3BUCKET} \
                    --stack-name ${STACKNAME} \
                    --capabilities CAPABILITY_IAM \
                    --region $AWS_DEFAULT_REGION \
                    --parameter-overrides \
                      LambdaFunctionName=${LambdaFunctionName} \
                      AwsRegion=${AWS_DEFAULT_REGION} \
                      VectorBucket=${VECTOR_BUCKET} \
                      IndexName=${INDEX_NAME} \
                      AWSAccountId=${AWS_ACCOUNT_ID}
                '''
            }
        }
    }
    }
    post {
        failure {
            echo 'Deployment failed.'
        }
        success {
            echo 'Deployment succeeded.'
        }
    }
}