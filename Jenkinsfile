pipeline {
    agent any

    environment {
        // The ID of the credential stored in Jenkins (e.g., Username with password / Personal Access Token)
        GITHUB_CREDENTIALS_ID = 'github-credentials-id'
        REPO_URL = 'https://github.com/Shivam5560/Professional_Grade_RAG.git'
    }

    stages {
        stage('Checkout') {
            steps {
                // Check out the code securely using Jenkins credentials
                git credentialsId: "${GITHUB_CREDENTIALS_ID}", url: "${REPO_URL}", branch: 'main'
            }
        }

        stage('Install Backend Dependencies') {
            steps {
                dir('backend') {
                    sh 'python3 -m venv venv'
                    sh '. venv/bin/activate && pip install -r requirements.txt'
                }
            }
        }

        stage('Install Frontend Dependencies') {
            steps {
                dir('frontend') {
                    sh 'npm install'
                }
            }
        }

        stage('Build Frontend') {
            steps {
                dir('frontend') {
                    sh 'npm run build'
                }
            }
        }

        stage('Git Push Example') {
            // This stage demonstrates how you can securely push changes back to GitHub
            // using the credentials injected by Jenkins, avoiding auth prompts.
            steps {
                withCredentials([usernamePassword(credentialsId: "${GITHUB_CREDENTIALS_ID}", passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                    sh '''
                        # Configure Git identity for the Jenkins bot
                        git config user.name "Jenkins Build Bot"
                        git config user.email "jenkins@localhost"
                        
                        # Example: If you need to make changes during the build and push them:
                        # git commit -am "chore: automated update from Jenkins"
                        
                        # Push changes back to the remote branch securely using injected credentials
                        git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/Shivam5560/Professional_Grade_RAG.git HEAD:main
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
