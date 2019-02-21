import deployer_cli

from app.const import TENANT_ID
from app.deployer.clients import images


def start_job(app_config, project_id, repo_url, test_config_id) -> deployer_cli.ImageBuildTaskSchema:
    data = deployer_cli.ImageBuildRequestSchema(
        repo_url=repo_url,
        tenant_id=TENANT_ID,
        project_id=project_id,
        start_proper_job=True,
        test_run_execution_id=test_config_id,
    )
    return images(app_config).image_builds_post(image_build_request_schema=data)
