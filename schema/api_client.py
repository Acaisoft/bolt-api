import string

from schema import upstream
from gql import gql


class BoltAPIClient(object):
    """
    GraphQL client for communication with Bolt database
    """

    def __init__(self, gql_client):
        self._gcl_client = gql_client

    def insert_user(self, data) -> str:
        """
        :param data: Dict:
            - email: str
            - active: bool
        :return: id
        """
        objects = upstream.user.Query(self._gcl_client)
        ret = objects.insert(upstream.user.User(**data))
        return ret[0]['id']

    def insert_aggregated_results(self, data):
        """
        :param data: Dict:
            - execution_id: uuid
            - fail: int
            - av_resp_time: float
            - succes: int
            - error: int
            - av_size: float
            - timestamp: int
        :return: id
        """
        objects = upstream.result_aggregate.Query(self._gcl_client)
        data = objects.input_type(**data)
        objects.insert(data)

    def insert_distribution_results(self, data):
        """
        :param data: Dict:
            - execution_id: uuid
            - start: datetime
            - end: datetime
            - request_result: struct/json
            - distribution_result: struct/json
        :return: id
        """
        objects = upstream.result_distribution.Query(self._gcl_client)
        data = upstream.result_distribution.ResultDistribution(**data)
        objects.insert(data)

    def insert_project(self, data):
        """
        :param data: Dict:
            - name: str
            - contact: str
        :return: id
        """
        ret = upstream.project.Query(self._gcl_client).insert(upstream.project.Project(**data))
        return ret[0]['id']

    def insert_repository(self, data):
        """
        :param data: Dict:
            - name: str
            - url: str
            - username: str
            - password: str
        :return: id
        """
        o = upstream.repository.Query(self._gcl_client)
        ret = o.insert(upstream.repository.Repository(**data))
        return ret[0]['id']

    def insert_configuration(self, data):
        """
        :param data: Dict:
            - name: str
            - project_id: uuid
            - repository_id: uuid
        :return: id
        """
        ret = upstream.configuration.Query(self._gcl_client).insert(
            upstream.configuration.Conf(**data)
        )
        return ret[0]['id']

    def insert_execution(self, data):
        """
        :param data: Dict:
            - configuration: uuid
        :return: id
        """
        query = string.Template('''mutation{insert_execution(objects:[{
        configuration_id:"$configuration",
        status:"running",
        }]) {returning {id}}}''').substitute(**data)
        ret = self._gcl_client.execute(gql(query))
        return ret['insert_execution']['returning'][0]['id']
