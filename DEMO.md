# BOLT-DEMO

Steps to go through to perform a demo test, through hasura console, without frontend.


#### Assuming hasura is up and user has admin role

* create a clean project

```
mutation {
  insert_project(objects:[{
    name:"testing att-lwd-go-dev.acaisoft.net",
    contact:"piotrek.monko@gmail.com"
  }]) {
    returning {id}
  }
}

>>> { "id": "539ce975-3b0b-400a-b6b6-8d8e101dd2f3" }
```

* assign your user to project

* create repository configuration

```
mutation {
  insert_repository (objects:[{
    name:"load-events repo",
    url:"git@bitbucket.org:acaisoft/load-events.git",
    project_id:"539ce975-3b0b-400a-b6b6-8d8e101dd2f3",
    type_id:"efd2d85d-ce7c-4db7-9fc9-0f4d687ba96b",
  }]) {returning { id }}
}

>>> { "id": "f1315b58-b463-4a45-a9bc-8cfecd733ecb" }
```

* create configuration

```
mutation {
  testrun_configuration_create(
    name:"att-lwd-go-dev 1",
    project_id:"539ce975-3b0b-400a-b6b6-8d8e101dd2f3",
    repository_id:"3b33b8fe-11ef-439a-8279-73337cbaaf7a",
    configurationParameters:[
    	{
        value:"100",  // 100 seconds 
        parameter_id:"04e3b56e-06a7-49aa-990b-5685873c548e"
      },
      {
        value:"https://att-lwd-go-dev.acaisoft.net/api",
        parameter_id:"adba8577-913c-447b-ae4d-3ab8934182e5"
      }
  	]
  ) { id }
}

>>> { "id": "46dc713e-ed81-412c-9c7e-4ff798652830" }
```

* start execution of test configuration

```
mutation {
  testrun_start (confId:"46dc713e-ed81-412c-9c7e-4ff798652830") {
    executionId
  }
}

>>> { "executionId": "8d53523c-5f94-4863-a6ce-17c5e9ef5301" }
```

* query execution state

```
query {
  testrun_status(executionId:"8d53523c-5f94-4863-a6ce-17c5e9ef5301") {
    status
  }
}

>>>    {
          "data": {
            "testrun_status": {
              "status": "PENDING"
            }
          }
        }
```

* and query execution state details (these are updated by calls to `testrun_status`)

```
query {
  execution_by_pk(id:"8d53523c-5f94-4863-a6ce-17c5e9ef5301") {
    status
    test_job_id
    test_preparation_job_id
    test_preparation_job_error
    test_preparation_job_status
    test_preparation_job_statuscheck_timestamp
  }
}

>>> {
    "data": {
        "execution_by_pk": {
          "status": "STARTED",
          "test_job_id": "d6b0b676-818f-4018-b8f0-1dcd373c61de",  ← id of testrun job
          "test_preparation_job_id": "6e32c6d6-bf99-49f3-a212-63c31cb8e878",
          "test_preparation_job_error": null,  ← image has been built without errors
          "test_preparation_job_status": "SUCCESS",  ← image has been built
          "test_preparation_job_statuscheck_timestamp": "2019-02-26T12:10:03.795135+00:00"
        }
      }
    }
```

* once execution_by_pk returns `"status": "STARTED"`, further calls to `testrun_status` are pointless 
and execution results should be fetched from `result_*` tables for given execution id
