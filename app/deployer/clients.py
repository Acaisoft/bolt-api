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


def management(config):
    return deployer_cli.ManagementApi(client(config))


def healthcheck(config):
    return deployer_cli.HealthCheckApi(client(config))
