import datetime

from gql.transport.requests import RequestsHTTPTransport
from gql import Client

from bolt_api import client

URL = 'http://localhost:8080/v1alpha1/graphql'

gql_client = Client(retries=0, transport=RequestsHTTPTransport(url=URL, use_json=True))
bolt_api_client = client.BoltAPIClient(gql_client=gql_client)


if __name__ == "__main__":
    # insert new user
    user = bolt_api_client.insert_user({'email': 'test@email.com', 'active': True})
    print(f'User result {user}')
    # insert new project
    project = bolt_api_client.insert_project({'name': 'project-name', 'contact': 'test@email.com'})
    print(f'Project result {project}')
    # insert new repository
    repository = bolt_api_client.insert_repository(
        {'name': 'repo 1', 'url': 'http://url.com/hello', 'username': 'root', 'password': 'root'})
    print(f'Repository result {repository}')
    # insert new configuration
    configuration = bolt_api_client.insert_configuration(
        {'name': 'conf-1', 'repository_id': repository, 'project_id': project})
    print(f'Configuration result {configuration}')
    # insert new execution
    execution = bolt_api_client.insert_execution({'configuration': configuration})
    print(f'Execution result {execution}')
    # insert new aggregated results
    aggregated_results = bolt_api_client.insert_aggregated_results({
        'execution_id': execution,
        'fail': 5,
        'succes': 10,
        'error': 15,
        'av_resp_time': 12.34,
        'av_size': 14,
        'timestamp': 1231231
    })
    print(f'Aggregated results {aggregated_results}')
    # insert new distribution results
    distribution_results = bolt_api_client.insert_distribution_results({
        'execution_id': execution,
        'start': datetime.datetime.now(),
        'end': datetime.datetime.now(),
        'request_result': {'hello': 'world'},
        'distribution_result': {'test': [1, 2, 3, 4]}
    })
    print(f'Distribution results {distribution_results}')
    # insert new error results
    error_results = bolt_api_client.insert_error_results({
        'execution_id': execution,
        'name': 'error name',
        'error_type': 'error type',
        'exception_data': '{}',
        'number_of_occurrences': 150
    })
    print(f'Error results {error_results}')
