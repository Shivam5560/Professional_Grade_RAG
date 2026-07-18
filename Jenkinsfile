pipeline {
    agent any

    parameters {
        string(
            name: 'GIT_REPOSITORY',
            defaultValue: 'https://github.com/Shivam5560/Professional_Grade_RAG.git',
            description: 'Read-only Git repository URL'
        )
        string(
            name: 'GIT_BRANCH',
            defaultValue: 'enhancements',
            description: 'Git branch to verify and package'
        )
    }

    environment {
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
    }

    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 90, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                git url: "${params.GIT_REPOSITORY}", branch: "${params.GIT_BRANCH}"
                script {
                    env.REPO_URL = params.GIT_REPOSITORY
                    env.SOURCE_COMMIT = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    def safeBranch = params.GIT_BRANCH.replaceAll(/[^A-Za-z0-9_.-]/, '-')
                    env.IMAGE_TAG = "${safeBranch}-${env.SOURCE_COMMIT.take(12)}-${env.BUILD_NUMBER}"
                }
            }
        }

        stage('CI Contract Tests') {
            steps {
                sh "python3 -m unittest discover -s scripts/ci -p 'test_*.py' -v"
            }
        }

        stage('Backend Tests') {
            steps {
                dir('backend') {
                    sh '''
                        python3 -m venv .jenkins-venv
                        . .jenkins-venv/bin/activate
                        python -m pip install -r requirements.txt pytest
                        PYTHONPATH=. python -m pytest \
                            tests/platform \
                            tests/studios/data_analyst \
                            tests/studios/career \
                            -q
                    '''
                }
            }
        }

        stage('Frontend Tests and Build') {
            steps {
                dir('frontend') {
                    sh '''
                        npm ci
                        npm test -- --pool=forks --maxWorkers=1
                        npm run typecheck
                        npm run build
                    '''
                }
            }
        }

        stage('MCP Build') {
            steps {
                dir('mcp-server') {
                    sh '''
                        npm ci
                        npm run build
                    '''
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    docker build \
                        --label "org.opencontainers.image.revision=${SOURCE_COMMIT}" \
                        --label "org.opencontainers.image.source=${REPO_URL}" \
                        --tag "nexusmind-backend:${IMAGE_TAG}" \
                        backend
                    docker run --rm \
                        --network none \
                        --read-only \
                        --cap-drop=ALL \
                        --security-opt no-new-privileges \
                        --entrypoint gunicorn \
                        "nexusmind-backend:${IMAGE_TAG}" \
                        --version
                    docker build \
                        --label "org.opencontainers.image.revision=${SOURCE_COMMIT}" \
                        --label "org.opencontainers.image.source=${REPO_URL}" \
                        --tag "nexusmind-frontend:${IMAGE_TAG}" \
                        frontend
                '''
            }
        }

        stage('Package Deployment Artifacts') {
            steps {
                sh '''
                    mkdir -p artifacts
                    docker save "nexusmind-backend:${IMAGE_TAG}" \
                        | gzip -9 > "artifacts/nexusmind-backend-${IMAGE_TAG}.tar.gz"
                    docker save "nexusmind-frontend:${IMAGE_TAG}" \
                        | gzip -9 > "artifacts/nexusmind-frontend-${IMAGE_TAG}.tar.gz"
                    tar -czf "artifacts/nexusmind-mcp-${IMAGE_TAG}.tar.gz" \
                        -C mcp-server dist package.json package-lock.json
                    sha256sum artifacts/*.tar.gz > artifacts/SHA256SUMS
                    printf 'branch=%s\ncommit=%s\nimage_tag=%s\n' \
                        "${GIT_BRANCH}" "${SOURCE_COMMIT}" "${IMAGE_TAG}" \
                        > artifacts/BUILD_MANIFEST.txt
                '''
                archiveArtifacts artifacts: 'artifacts/*', fingerprint: true
            }
        }
    }

    post {
        always {
            sh '''
                if [ -n "${IMAGE_TAG:-}" ]; then
                    docker image rm \
                        "nexusmind-backend:${IMAGE_TAG}" \
                        "nexusmind-frontend:${IMAGE_TAG}" \
                        >/dev/null 2>&1 || true
                fi
            '''
            cleanWs(deleteDirs: true)
        }
        success {
            echo "Deployable artifacts created for ${params.GIT_BRANCH} at ${env.SOURCE_COMMIT}."
        }
        failure {
            echo 'Pipeline failed before deployable artifacts could be published.'
        }
    }
}
