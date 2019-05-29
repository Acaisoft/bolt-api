import os

from services import const
from services.testing.testing_util import BoltCase


class TestExtentionMutations(BoltCase):

    def setUp(self) -> None:
        super().setUp()
        # disable keycloack integration as that communication returns random ids not suitable for vcr
        os.environ['SELFSIGNED_TOKEN_FOR_TESTRUNNER'] = '1'
        os.environ['SELFSIGNED_TOKEN_EXECUTION_ID'] = self.recorded_execution_id

    def tearDown(self) -> None:
        os.unsetenv('SELFSIGNED_TOKEN_FOR_TESTRUNNER')
        os.unsetenv('SELFSIGNED_TOKEN_EXECUTION_ID')