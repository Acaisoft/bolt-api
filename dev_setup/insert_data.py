import string

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from schema.upstream import user, result


def insert_users(client: Client):
    for i in range(100):
        ee = "u{}@acaisoft.pl".format(i)
        qq = user.upsert.substitute(email=ee, active="true")
        rr = client.execute(gql(qq))
        print(rr)


def insert_user(client: Client) -> str:
    objects = user.User(client)
    ret = objects.insert(objects.input_type(email="admin@acaisoft.net", active="true"))
    return ret['insert_user']['returning'][0]['id']


def insert_execution_results(client: Client, execution_id):
    dd = result.Result(client)
    data_set = []
    for i in range(10000):
        data_set.append(dd.input_type(
            execution_id=execution_id,
            endpoint="/stats/",
            exception="",
            request_type="GET",
            response_length=123,
            response_time=12.34,
            status="200",
            timestamp=1231231231321,
        ))
    dd.bulk_insert(data_set)


def insert_project(client):
    ret = client.execute(
        gql('mutation{insert_project(objects:[{name:"project1", contact:"admin@adm.in"}]) {returning {id}}}'))
    return ret['insert_project']['returning'][0]['id']


def insert_repository(client):
    ret = client.execute(
        gql('mutation{insert_repository(objects:[{name:"repo1", url:"http://url.url", username:"admin", password:"secret"}]) {returning {id}}}'))
    return ret['insert_repository']['returning'][0]['id']


def insert_configuration(client, project, repository):
    query = string.Template('''mutation{insert_configuration(objects:[{
    name:"conf1", 
    repository_id:"$repo",
    project_id:"$project",
    }]) {returning {id}}}''').substitute(repo=repository, project=project)
    ret = client.execute(gql(query))
    return ret['insert_configuration']['returning'][0]['id']


def insert_execution(client, configuration):
    query = string.Template('''mutation{insert_execution(objects:[{
    configuration_id:"$configuration",
    status:"running",
    }]) {returning {id}}}''').substitute(configuration=configuration)
    ret = client.execute(gql(query))
    return ret['insert_execution']['returning'][0]['id']


def insert_data(client: Client):
    # insert_users(client)
    admin_user = insert_user(client)
    project = insert_project(client)
    repository = insert_repository(client)
    configuration = insert_configuration(client, project, repository)
    execution = insert_execution(client, configuration)
    insert_execution_results(client, execution)


def purge_data(client: Client):
    client.execute(gql(user.purge.substitute()))


def new_client() -> Client:
    return Client(
        retries=0,
        transport=RequestsHTTPTransport(
            url='http://localhost:8080/v1alpha1/graphql',
            use_json=True
        )
    )


if __name__ == "__main__":
    cl = new_client()
    # purge_data(cl)
    insert_data(cl)
