import json
import os
import unittest

from services.exports import data_extractor


class TestDataExtractor(unittest.TestCase):

    @staticmethod
    def _get_fixture(fixture_path):
        here = os.path.dirname(__file__)
        path = os.path.join(here, 'fixtures', fixture_path)
        with open(path, 'r') as f:
            return json.load(f)

    def test_nfs_extractor(self):
        """
        Assert that nfs extension additional data results are correctly converted from database representation of
            [{[{data}, {more data}, {...}]}, {[{another data}, {more another data}, {...}]}]
        to a flat
            [{data}, {more data}, {...}, {another data}, {more another data}, {...}]
        """
        nfs = self._get_fixture('execution_additional_data_nfs.json')
        out = data_extractor.convert_data('nfs', [{'data': nfs}])
        # assert each element is a flat dict of ints or floats and sorted by timestamp
        prev_ts = 0
        for i in out:
            assert type(i) is dict, f'expected a dict, got {str(type(i))}'

            ts = i.get('timestamp', None)
            assert type(ts) in (int, float), f'timestamp missing or invalid type'
            assert prev_ts > ts, f'expected output to be ordered by timestamp'
            prev_ts = ts

            for k, v in i.items():
                assert type(k) is str, f'expected a string key, got {k}'
                assert type(v) in (int, float), f'expected a numeric value, got {type(v)} == {v}'
