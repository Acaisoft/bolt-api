Changelog
=========

## (unreleased)

### Changes

* Allow change to repository url if not yet performed. [Piotr Mońko]

### Fix

* Fix signed url upload method. [Piotr Mońko]

### Other

* Add create/_validate and update/_validate methods for repository. [Piotr Mońko]


## 0.1.3 (2019-03-20)

### Changes

* Add testrun_project_image_upload implementation. [Piotr Mońko]

* Refactor hasura connection names. [Piotr Mońko]

### Fix

* Fix some non-camelcase hasura relation names. [Piotr Mońko]

### Other

* Add create/_validate and update/_validate methods for repository. [Piotr Mońko]

* Update changelog. [Piotr Mońko]


## 0.1.2 (2019-03-18)

### Changes

* Add common Interface for typed schema responses. [Piotr Mońko]

* Add testrun_project_image_upload stub method placeholder. [Piotr Mońko]

* Wrap project_create and configuration_create in ReturnTypes with .returning members. [Piotr Mońko]

* Rename configurationParams relation to configuration_params. [Piotr Mońko]

### Other

* Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr Mońko]

* Add testrun_project_image_upload stub method placeholder. [Piotr Mońko]

* Update changelog. [Piotr Mońko]

* Add testrun_project_create and testrun_project_create_validate. [Piotr Mońko]

* Change: rename configurationParams relation on configuration to configuration_params. [Piotr Mońko]


0.1.0 (2019-03-15)
-------------------
- Update readme. [Piotr Mońko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Delete bolt_api catalog from Dockerfile. [art.barysevich]
- Merged in refactoring-test-creator (pull request #7) [Artiom
  Borysiewicz]

  Refactoring Test Creator
- Configuration update endpoints. [Piotr Mońko]
- Change test_creator to match by m2m. [Piotr Mońko]
- Merged in validation-for-test-creator (pull request #6) [Artiom
  Borysiewicz]

  Add validators for TestCreator
- Add validators for TestCreator. [art.barysevich]
- Test_creator validations. [Piotr Mońko]
- Add scaffold for test_creator graphql mutation, add test_creator
  table. [Piotr Mońko]
- Record commit_hash. [Piotr Mońko]
- Fix invalid key. [Piotr Mońko]
- Handle multiple auth id in hasura. [Piotr Mońko]
- Fix invalid import. [Piotr Mońko]
- Add repository connectivity test at validation time. [Piotr Mońko]
- Add no_cache. [Piotr Mońko]
- Update bolt-deployer version, add performed flag -check. [Piotr Mońko]
- Fix CRASHED in testrun status. [Piotr Mońko]
- Setup update testrun_status callback. [Piotr Mońko]
- Fix nonrefreshing schema. [Piotr Mońko]
- Upgrade from raven to sentrysdk. [Piotr Mońko]
- Add sentry_check command. [Piotr Mońko]
- Add test job error to execution, fix job status. [Piotr Mońko]
- Add project validators, refactor configuration validators. [Piotr
  Mońko]
- Fix missing requirement. [Piotr Mońko]
- Fix invalid gitmodule. [Piotr Mońko]
- Delete users table. [Piotr Mońko]
- Remove job status return value for running tests. [Piotr Mońko]
- Allow admin to start any configurateion testrun. [Piotr Mońko]
- Allow admin to start any configurateion testrun. [Piotr Mońko]
- Use only first role. [Piotr Mońko]
- Remove user id validation for testing. [Piotr Mońko]
- Remove hasura endpoint. [Piotr Mońko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Refactor helm chart and jenkinsfile. #DO-51. [Kamil Litwiniuk]
- Describe DEMO steps. [Piotr Mońko]
- Fix migrations. [Piotr Mońko]
- Remove teporarily configuration insertion. [Piotr Mońko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Merged in refactoring-graphql-queries (pull request #4) [Artiom
  Borysiewicz]

  Refactoring. Add tests for serializing data
- Merge from master. [art.barysevich]
- Refactoring. Add tests for serializing data. [art.barysevich]
- Update config. [jroslaniec-acaisoft]
- Fix - Decrypt secrets in Jenkins. [jroslaniec-acaisoft]
- Fix secrets. [jroslaniec-acaisoft]
- Add unified status interface, add consolidated configuration
  validation. [Piotr Mońko]
- Add config and secret versions. [Piotr Mońko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Revert "Revert "Revert "Change submodule to https""" [jroslaniec-
  acaisoft]

  This reverts commit 3af5a42e3a719b666785749eb0531052856d09d0.
- Revert "Revert "Change submodule to https"" [jroslaniec-acaisoft]

  This reverts commit 4fdcf9f85aae621d02b064195931ec5735e81f58.
- Revert "Change submodule to https" [jroslaniec-acaisoft]

  This reverts commit 6fd95cb87ae2f5a814a3eeac44aa167047d8620f.
- Change submodule to https. [jroslaniec-acaisoft]
- Add logging. [Piotr Mońko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Update submodule user. [jroslaniec-acaisoft]
- Add dev deployment to k8s. [jroslaniec-acaisoft]
- Remove personal id. [Piotr Mońko]
- Add endpoint for obtaining key, checking job status. [Piotr Mońko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Add default type_id to repository. [mateuszbernat]
- Add configuration type relation to repository. [mateuszbernat]
- Removed username and password fields from repository table, added
  performed field to repository and configurations tables.
  [mateuszbernat]
- Add bolt_deployer healthcheck. [Piotr Mońko]
- Moved type from configurations to repositories. [mateuszbernat]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Piotr
  Mońko]
- Add REDIS_PASS to secrets. [jroslaniec-acaisoft]
- Add redis password. [Piotr Mońko]
- Fix imports. [Piotr Mońko]
- Merge branch 'acbt-26-start-test' [Piotr Mońko]
- Refactor configuration. [Piotr Mońko]
- Merge remote-tracking branch 'origin/master' into acbt-26-start-test.
  [Piotr Mońko]
- Refs #acbt-26. wip. [Piotr Mońko]
- Add helm chart. [jroslaniec-acaisoft]
- Add Jenkinsfile. [jroslaniec-acaisoft]
- Merged in fix-upstreams-and-api-client (pull request #3) [Artiom
  Borysiewicz]

  Fix arguments for upstreams. Modify client for bolt-api. Fix fields
- Fix arguments for upstreams. Modify client for bolt-api. Fix fields.
  [art.barysevich]
- Add permissions and more tables. [Piotr Mońko]
- Refactor some column names. [Piotr Mońko]
- Remove leftovers. [Piotr Mońko]
- Add example instance configuration. [Piotr Mońko]
- Some updates. [Piotr Mońko]
- Fix double handler. [Peter Monko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Peter
  Monko]
- Merged in add-result-error-table (pull request #2) [Artiom
  Borysiewicz]

  Add result_error table, migrations and function for client
- Add result_error table, migrations and function for client.
  [art.barysevich]
- Add permissions again. [Peter Monko]
- Add permissions. [Peter Monko]
- Refactor structure. [Peter Monko]
- Merged in api-client (pull request #1) [Artiom Borysiewicz]

  Add python client for bolt api
- Add python client for bolt api. [art.barysevich]
- Remote schema poc. [Piotr Mońko]
- Change uwsgi to gunicorn. [Piotr Mońko]
- Add result_distribution and helpers. [Piotr Mońko]
- Add user, project, conf views. [Peter Monko]
- Merge branch 'master' of bitbucket.org:acaisoft/bolt-api. [Peter
  Monko]
- Add more upstreams. [Piotr Mońko]
- Add result aggregate. [Piotr Mońko]
- Add bare hasura dockerfile. [Peter Monko]
- Add python requirements. [Peter Monko]
- Initial. [Peter Monko]


