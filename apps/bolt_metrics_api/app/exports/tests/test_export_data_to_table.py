import json
import os
import unittest

from apps.bolt_metrics_api.app.exports.graphana_simple_json import dataset_to_timeserie, dataset_to_table


class TestExportDataToTable(unittest.TestCase):

    @staticmethod
    def _get_fixture(fixture_path):
        here = os.path.dirname(__file__)
        path = os.path.join(here, 'fixtures', fixture_path)
        with open(path, 'r') as f:
            return json.load(f)

    def test_table(self):
        targets = [
            'timeserie:timestamp', 'timeserie:number_of_errors',
            'errors:name', 'errors:number_of_occurrences',
            'requests:timestamp', 'requests:num_requests', 'requests:num_failures',
            'distributions:timestamp', 'distributions:num_requests', 'distributions:p100',
        ]
        dataset = self._get_fixture('single_execution_data.json')
        output = dataset_to_table(dataset['execution'][0], targets)
        actual = json.dumps(output)
        expected = json.dumps(self._get_fixture('expected_test_table.json'))
        self.assertEqual(expected, actual)

    def test_timeseries(self):
        targets = [
            'timeserie:timestamp', 'timeserie:number_of_errors',
            'requests:timestamp', 'requests:num_requests', 'requests:num_failures',
            'distributions:timestamp', 'distributions:num_requests', 'distributions:p100',
        ]
        dataset = self._get_fixture('single_execution_data.json')
        output = dataset_to_timeserie(dataset['execution'][0], targets)
        actual = json.dumps(output)
        expected = json.dumps(self._get_fixture('expected_test_timeseries.json'))
        self.assertEqual(expected, actual)
