import json
import unittest

from services.exports import data_extractor


class TestTestCreatorValidation(unittest.TestCase):

    @staticmethod
    def _get_fixture(fixture_path):
        with open(fixture_path, 'r') as f:
            return json.load(f)

    def test_nfs_extractor(self):
        nfs = self._get_fixture('fixtures/execution_additional_data_nfs.json')
        out = data_extractor.convert_data('nfs', [{'data': nfs}])
        print(out)
