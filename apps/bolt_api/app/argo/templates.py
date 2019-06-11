import yaml

MASTER_SLAVE_TEMPLATE = '''
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: bolt-master- 
  annotations:
    jwt: __JWT__
    executionId: __EXECUTION_ID__
    tenantId: __TENANT_ID__
    projectId: __PROJECT_ID__
    repositoryUrl: __REPOSITORY_URL__
spec:
  entrypoint: main 
  onExit: exit-handler
  volumes:
    - name: ssh
      secret:
        secretName: ssh-files
        defaultMode: 0600
    - name: kaniko-secret
      secret:
        secretName: kaniko-secret
  templates:
  - name: main
    steps:
      - - name: locust-builder
          template: builder

      - - name: locust-tests
          template: locust-tests

  - name: locust-tests
    dag:
      tasks:
      - name: locust-master
        template: master

  - name: exit-handler
    steps:
        - - name: notify
            template: print-message
            arguments:
              parameters:
              - name: message
                value: "Exit notification"

  - name: master              
    daemon: true
    container:
      image: "{{workflow.outputs.parameters.image}}"
      imagePullPolicy: IfNotPresent
      command: ["python", "-m", "bolt_run", "load_tests"]
      env:
        - name: BOLT_EXECUTION_ID
          value: "{{workflow.annotations.executionId}}"
        - name: BOLT_GRAPHQL_URL
          value: http://hasura.hasura.svc.cluster.local/v1alpha1/graphql
        - name: BOLT_HASURA_TOKEN
          value: "{{workflow.annotations.jwt}}"
        - name: BOLT_WORKER_TYPE
          value: master
      resources:               
        limits:
          memory: 512Mi
          cpu: 300m
        requests:
          memory: 512Mi
          cpu: 200m
    nodeSelector:
        group: load-tests-workers-master

  - name: slave             
    inputs:
      parameters:
        - name: master-ip
    container:
      image: "{{workflow.outputs.parameters.image}}"
      imagePullPolicy: IfNotPresent
      command: ["python", "-m", "bolt_run", "load_tests"]
      env:
        - name: BOLT_EXECUTION_ID
          value: "{{workflow.annotations.executionId}}"
        - name: BOLT_GRAPHQL_URL
          value: http://hasura.hasura.svc.cluster.local/v1alpha1/graphql
        - name: BOLT_HASURA_TOKEN
          value: "{{workflow.annotations.jwt}}"
        - name: BOLT_WORKER_TYPE
          value: slave
        - name: BOLT_MASTER_HOST
          value: "{{inputs.parameters.master-ip}}"
      resources:               
        limits:
          memory: 2Gi
          cpu: 900m
        requests:
          memory: 2Gi
          cpu: 800m
    nodeSelector:
        group: load-tests-workers-slave

  - name: builder
    container:
      image: "eu.gcr.io/acai-bolt/argo-builder"
      imagePullPolicy: Always
      env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /etc/kaniko/kaniko-secret.json
        - name: CLOUDSDK_CORE_PROJECT
          value: acai-bolt
        - name: PROJECT_ID
          value: "{{workflow.annotations.projectId}}"
        - name: TENANT_ID
          value: "{{workflow.annotations.tenantId}}"
        - name: REPOSITORY_URL
          value: "{{workflow.annotations.repositoryUrl}}"
      volumeMounts:
        - name: ssh
          mountPath: /root/.ssh
        - name: kaniko-secret
          mountPath: /etc/kaniko/
    outputs:
      parameters:
      - name: image
        valueFrom:
          path: /tmp/image.txt
        globalName: image

  - name: monitoring              
    daemon: true
    container:
      image: "{{workflow.outputs.parameters.image}}"
      imagePullPolicy: IfNotPresent
      command: ["python", "-m", "bolt_run", "monitoring"]
      env:
        - name: BOLT_EXECUTION_ID
          value: "{{workflow.annotations.executionId}}"
        - name: BOLT_GRAPHQL_URL
          value: http://hasura.hasura.svc.cluster.local/v1alpha1/graphql
        - name: BOLT_HASURA_TOKEN
          value: "{{workflow.annotations.jwt}}"
        - name: BOLT_WORKER_TYPE
          value: master
      resources:               
        limits:
          memory: 2Gi
          cpu: 900m
        requests:
          memory: 2Gi
          cpu: 800m
    nodeSelector:
        group: load-tests-workers-slave

  - name: print-message
    inputs:
      parameters:
          - name: message
    container:
      image: alpine:latest
      command: [sh, -c]
      args: ["echo result was: {{inputs.parameters.message}}"]
    priorityClassName: argo-job-policy
'''


def get_master_slave_template(jwt, execution_id, tenant_id, project_id, repository_url):
    tmp = MASTER_SLAVE_TEMPLATE.replace('__JWT__', str(jwt))
    tmp = tmp.replace('__EXECUTION_ID__', str(execution_id))
    tmp = tmp.replace('__TENANT_ID__', str(tenant_id))
    tmp = tmp.replace('__PROJECT_ID__', str(project_id))
    tmp = tmp.replace('__REPOSITORY_URL__', str(repository_url))
    return yaml.load(tmp, Loader=yaml.FullLoader)
