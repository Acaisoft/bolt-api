import deployer_cli


def client(config):
    conf = deployer_cli.Configuration()
    conf.host = config.get('BOLT_DEPLOYER_ADDR')
    conf.api_key['Authorization'] = config.get('BOLT_DEPLOYER_TOKEN')
    conf.api_key_prefix['Authorization'] = 'Bearer'
    return deployer_cli.ApiClient(conf)


def jobs(config):
    return deployer_cli.JobsApi(client(config))


def images(config):
    return deployer_cli.ImageBuildsApi(client(config))


def healthcheck(config):
    return deployer_cli.HealthCheckApi(client(config))


def start_job(app_config, project_id, repo_url, test_config_id) -> deployer_cli.ImageBuildTaskSchema:
    data = deployer_cli.ImageBuildRequestSchema(
        repo_url=repo_url,
        tenant_id=project_id,
        project_id=project_id,
        start_proper_job=True,
        test_run_execution_id=test_config_id,
    )
    return images(app_config).image_builds_post(image_build_request_schema=data)
