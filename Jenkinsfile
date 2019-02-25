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

        stage('Prepare') {
            withCredentials([file(credentialsId: '.bolt_key', variable: 'BOLT_KEY')]) {
                sh "ln -s ${BOLT_KEY} .bolt_key"
                sh "bin/decrypt"
            }
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

        stage('Deploy') {
			if (env.BRANCH_NAME == DEV_BRANCH) {
				echo "Deploy to dev"
                withCredentials([file(credentialsId: DEV_SERVICE_ACCOUNT_KEY, variable: 'KEY_FILE')]) {
                    docker.withRegistry("${GCR_URL}", "gcr:${GCR_CREDENTIALS}") {
                        docker.image(JENKINS_DEPLOYER_IMAGE).inside("-v ${WORKSPACE}/gcloud:/.config/gcloud -v ${WORKSPACE}/kube:/.kube -u root") {
                            sh "/root/google-cloud-sdk/bin/gcloud auth activate-service-account ${DEV_SERVICE_ACCOUNT} --key-file=${KEY_FILE}"
                            sh "/root/google-cloud-sdk/bin/gcloud container clusters get-credentials ${DEV_CLUSTER_NAME} --zone ${DEV_ZONE} --project ${DEV_GCP_PROJECT}"
                            sh "helm upgrade dev-bolt-api charts/bolt-api --set image.tag=${version} --wait --timeout 600"
                        }
                    }
                }
				return;
			}

            // if (env.BRANCH_NAME == PROD_BRANCH) {
			// 	echo "Deploy to prod"
            //     withCredentials([file(credentialsId: PROD_SERVICE_ACCOUNT_KEY, variable: 'KEY_FILE')]) {
            //         docker.withRegistry("${GCR_URL}", "gcr:${GCR_CREDENTIALS}") {
            //             docker.image(JENKINS_DEPLOYER_IMAGE).inside("-v ${WORKSPACE}/gcloud:/.config/gcloud -v ${WORKSPACE}/kube:/.kube -u root") {
            //                 sh "gcloud auth activate-service-account ${PROD_SERVICE_ACCOUNT} --key-file=${KEY_FILE}"
            //                 sh "gcloud container clusters get-credentials ${PROD_CLUSTER_NAME} --zone ${PROD_ZONE} --project ${PROD_GCP_PROJECT}"
            //                 sh "helm upgrade prod-bolt-deployer charts/bolt-deployer --set image=${DOCKER_REPOSITORY}:${version} --wait --timeout 600"
            //             }
            //         }
            //     }
			// 	return;
			// }

            echo "Skipping. Runs only for ${DEV_BRANCH} and ${PROD_BRANCH} branches"
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
