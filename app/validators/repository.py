import requests

from app.deployer import clients


def validate_repository(user_id, repo_config):
    """
    >>> validate_repository('u1', {
    ...  "url": "http://url.url/url",
    ...  "configurationType": { "slug_name": "extreme_load" },
    ...  "project": {
    ...    "is_deleted": False,
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
    ...  "configurationType": { "slug_name": "extreme_load" },
    ...  "project": {
    ...    "is_deleted": False,
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
    assert len(repo_config['url']) > 5, f'invalid repository url ({repo_config["url"]})'

    assert is_user_project_valid(user_id, repo_config['project'])


def is_user_project_valid(user_id, project_config):
    assert not project_config['is_deleted'], 'invalid project, perhaps it has been deleted?'

    for up in project_config['userProjects']:
        if up['user_id'] == user_id:
            return True

    raise AssertionError('user has no access to project')


def validate_accessibility(repository_url, app_config):
    """
    Validate repo is accessible using the key provided by upstream bolt-deployer
    """
    # TODO: add endpoint in bolt-deployer which would call the repo using paramiko or even 'git ls-remote'
    # response = clients.management(app_config).management_validate_repo_access(repository_url)
    # assert response.status == 'OK'
    return


if __name__ == '__main__':
    import doctest

    doctest.testmod()
