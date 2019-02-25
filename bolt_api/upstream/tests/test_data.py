import datetime
import unittest

from bolt_api import upstream


class DataSerializeTestCase(unittest.TestCase):

    def test_data_configuration_serialize(self):
        data = upstream.configuration.Configuration(
            name='Conf-1', repository_id='repository_id', project_id='project_id', type_id='type_id')
        output = upstream.configuration.Query.serialize(data)
        self.assertEqual(output, '''{
name:"Conf-1",
repository_id:"repository_id",
project_id:"project_id",
type_id:"type_id",
},
''')

    def test_data_configuration_type_serialize(self):
        data = upstream.configuration_type.ConfigurationType(name='Conf type 1', description='Description conf type 1')
        output = upstream.configuration_type.Query.serialize(data)
        self.assertEqual(output, '''{
name:"Conf type 1",
description:"Description conf type 1",
},
''')

    def test_data_project_serialize(self):
        data = upstream.project.Project(name='Project name #1', contact='admin@acaisoft.com')
        output = upstream.project.Query.serialize(data)
        self.assertEqual(output, '''{
name:"Project name #1",
contact:"admin@acaisoft.com",
},
''')

    def test_data_repository_serialize(self):
        data = upstream.repository.Repository(name='name', url='http://url.name', username='username', password='pass')
        output = upstream.repository.Query.serialize(data)
        self.assertEqual(output, '''{
name:"name",
url:"http://url.name",
username:"username",
password:"pass",
},
''')

    def test_data_result_aggregate_serialize(self):
        data = upstream.result_aggregate.ResultAggregate(
            execution_id='1234-abc-567-zxy', number_of_fails='200', number_of_successes='100', number_of_errors='300',
            average_response_time='15.33', average_response_size='15.10', timestamp=datetime.datetime(2020, 1, 1)
        )
        output = upstream.result_aggregate.Query.serialize(data)
        self.assertEqual(output, '''{
execution_id:"1234-abc-567-zxy",
number_of_fails:"200",
number_of_successes:"100",
number_of_errors:"300",
average_response_time:"15.33",
average_response_size:"15.10",
timestamp:"2020-01-01T00:00:00",
},
''')

    def test_data_result_distribution_serialize(self):
        data = upstream.result_distribution.ResultDistribution(
            execution_id='1234-abc-5678-xyz',
            start=datetime.datetime(2020, 1, 1),
            end=datetime.datetime(2020, 1, 1),
            request_result={'hello': 'world', "test": "guest", 'dict': {"ttt": 'ttt'}},
            distribution_result={'test': {'data': [3, 2, 1]}}
        )
        output = upstream.result_distribution.Query.serialize(data)
        self.assertEqual(output, '''{
execution_id:"1234-abc-5678-xyz",
start:"2020-01-01T00:00:00",
end:"2020-01-01T00:00:00",
request_result:"{\\"hello\\": \\"world\\", \\"test\\": \\"guest\\", \\"dict\\": {\\"ttt\\": \\"ttt\\"}}",
distribution_result:"{\\"test\\": {\\"data\\": [3, 2, 1]}}",
},
''')

    def test_data_result_error_serialize(self):
        data = upstream.result_error.ResultError(
            execution_id='123-abc-567-xyz', name='error name', error_type='error type',
            exception_data='exc data', number_of_occurrences='number of acc')
        output = upstream.result_error.Query.serialize(data)
        self.assertEqual(output, '''{
execution_id:"123-abc-567-xyz",
name:"error name",
error_type:"error type",
exception_data:"exc data",
number_of_occurrences:"number of acc",
},
''')

    def test_data_user_serialize(self):
        data = upstream.user.User(email='jan@kowal.pl', active=True)
        output = upstream.user.Query.serialize(data)
        self.assertEqual(output, '''{
email:"jan@kowal.pl",
active:true,
},
''')

    def test_data_user_project_serialize(self):
        data = upstream.user_project.UserProject(user_id='1234', project_id='5678')
        output = upstream.user_project.Query.serialize(data)
        self.assertEqual(output, '''{
user_id:"1234",
project_id:"5678",
},
''')
