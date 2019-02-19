#!groovy

properties(
        [[$class  : 'BuildDiscarderProperty',
          strategy: [$class: 'LogRotator', artifactDaysToKeepStr: '15', artifactNumToKeepStr: '15', daysToKeepStr: '15', numToKeepStr: '15']]])

def JENKINS_DEPLOYER_IMAGE="eu.gcr.io/acai-bolt/bolt-jenkins-deployer:0.1.0"

def DOCKER_REPOSITORY = "eu.gcr.io/acai-bolt/bolt-api"
def GCR_CREDENTIALS = "acai-bolt-gcp-private-key"
def PROD_BRANCH = "prod"
def GCR_URL = "https://eu.gcr.io"

// TODO: Uncommnet and update for prod deployment
// def PROD_SERVICE_ACCOUNT = ""
// def PROD_SERVICE_ACCOUNT_KEY = ""
// def PROD_GCP_PROJECT = ""
// def PROD_CLUSTER_NAME = ""
// def PROD_ZONE = ""

def DEV_BRANCH = "master"
def DEV_SERVICE_ACCOUNT = "jenkins-deployer@acai-bolt.iam.gserviceaccount.com"
def DEV_SERVICE_ACCOUNT_KEY = "bolt-jenkins-deployer-sa-file"

def DEV_GCP_PROJECT = "acai-bolt"
def DEV_CLUSTER_NAME = "bol-dev"
def DEV_ZONE = "europe-west1-d"

node('docker') {
    env.COMPOSE_INTERACTIVE_NO_CLI = 1
    env.HOME = "${WORKSPACE}"

    def version = ''
    def errorMessage = ''

    try {
        stage('Clear workspace') {
            sh "printenv"
            deleteDir()
        }

        stage('Checkout') {
            retry(3) {
                checkout scm
            }
            version = sh returnStdout: true, script: 'git describe --long --dirty --abbrev=10 --tags --always'
            version = env.BRANCH_NAME + "-" + version.replaceAll("\\s+", "")
            echo "Version: ${version}"
        }

        stage('Build image') {
            if (env.BRANCH_NAME != DEV_BRANCH && env.BRANCH_NAME != PROD_BRANCH) {
                echo "Skipping. Runs only for ${DEV_BRANCH} and ${PROD_BRANCH} branches"
                return;
            }
            sh "docker build -t ${DOCKER_REPOSITORY}:${version} ."
        }

        stage('Push image') {
            if (env.BRANCH_NAME != DEV_BRANCH && env.BRANCH_NAME != PROD_BRANCH) {
                echo "Skipping. Runs only for ${DEV_BRANCH} and ${PROD_BRANCH} branches"
                return;
            }
            docker.withRegistry("${GCR_URL}", "gcr:${GCR_CREDENTIALS}") {
                sh "ln -s /home/acaisoft/.dockercfg ${env.HOME}/.dockercfg"
                sh "docker push ${DOCKER_REPOSITORY}:${version}"
            }
        }

    }
    catch (ex) {
        currentBuild.result = "FAILED"
        errorMessage = ex.getMessage()
        throw ex
    }
    finally {
        stage('Clean up') {
            cleanWs()
        }
    }
}
