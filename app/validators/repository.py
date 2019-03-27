import re

import deployer_cli
import requests

from app.deployer import clients


def validate_repository(user_id, repo_config):
    """
    >>> validate_repository('u1', {
    ...  "url": "http://url.url/url",
    ...  "configuration_type": { "slug_name": "extreme_load" },
    ...  "project": {
    ...    "userProjects": [
    ...      { "user_id": "4f2e6f44-9db9-47fd-a5c4-6c129ea70cc7" },
    ...    ]
    ...  }
    ... })
    Traceback (most recent call last):
    ...
    AssertionError: user has no access to project
    >>> validate_repository('u1', {
    ...  "url": "http://url.url/url",
    ...  "configuration_type": { "slug_name": "extreme_load" },
    ...  "project": {
    ...    "userProjects": [
    ...      { "user_id": "4f2e6f44-9db9-47fd-a5c4-6c129ea70cc7" },
    ...      { "user_id": "u1" },
    ...    ]
    ...  }
    ... })
    >>> validate_repository('u1', {"url": "abc"})
    Traceback (most recent call last):
    ...
    AssertionError: invalid repository url (abc)
    """
    regex = '((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?'
    assert re.match(regex, repo_config['url']), f'invalid repository url ({repo_config["url"]})'

    if user_id:
        assert is_user_project_valid(user_id, repo_config['project'])


def is_user_project_valid(user_id, project_config):
    for up in project_config['userProjects']:
        if up['user_id'] == user_id:
            return True

    raise AssertionError('user has no access to project')


def validate_accessibility(app_config, repository_url:str):
    """
    Validate repo is accessible using the key provided by upstream bolt-deployer
    """
    repository_url = repository_url.strip()
    regex = '((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?'
    assert re.match(regex, repository_url), f'invalid repository url ({repository_url})'

    req = deployer_cli.ValidateRepositorySchema(repository_url=repository_url)
    response = clients.management(app_config).management_validate_repository_post(validate_repository_schema=req)
    assert response.is_valid, f'it appears repository is not accessible ({str(response)})'
    return repository_url


if __name__ == '__main__':
    import doctest

    doctest.testmod()
