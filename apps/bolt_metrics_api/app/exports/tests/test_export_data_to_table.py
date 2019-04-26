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
        expected = '[' \
            '{"type": "table", ' \
            '"columns": [' \
                   '{"text": "Timeserie: Timestamp", "type": "time"}, ' \
                   '{"text": "Timeserie: Number Of Errors", "type": "number"}, ' \
                   '{"text": "Errors: Name", "type": "number"}, ' \
                   '{"text": "Errors: Number Of Occurrences", "type": "number"}, ' \
                   '{"text": "Requests: # Failures", "type": "number"}, ' \
                   '{"text": "Requests: Requests/S", "type": "number"}, ' \
                   '{"text": "Distributions: # Requests", "type": "number"}, ' \
                   '{"text": "Distributions: 98%", "type": "number"}], ' \
            '"rows": [[1556087456690.661, 0, "/send", 125, "385", "147.22", "385", "410"], ' \
                   '[1556087455006.854, 7, "/random", 243, "249", "95.22", "249", "370"], ' \
                   '[1556087453407.881, 7, "/", 385, "116", "44.36", "116", "380"], ' \
                   '[1556087451385.171, 0, "/error/404", 259, "145", "55.45", "145", "440"], ' \
                   '[0, 0, "/echo/hello", 249, "259", "99.04", "259", "380"], ' \
                   '[0, 0, "/error/401", 145, "243", "92.92", "243", "390"],' \
                   ' [0, 0, "/error/400or500", 116, "125", "47.80", "125", "370"],' \
                   ' [0, 0, 0, 0, 0, 0, "1522", "380"]]}]'
        self.assertEqual(expected, actual)

    def test_timeseries(self):
        targets = [
            'timeserie:timestamp', 'timeserie:number_of_errors',
            'errors:name', 'errors:number_of_occurrences',
            'requests:timestamp', 'requests:num_requests', 'requests:num_failures',
            'distributions:timestamp', 'distributions:num_requests', 'distributions:p100',
        ]
        dataset = self._get_fixture('single_execution_data.json')
        output = dataset_to_timeserie(dataset['execution'][0], targets)
        actual = json.dumps(output)
        expected = '[{"target": "timeserie:number_of_errors", "datapoints": [[0.0, 1556087456690.661], ' \
                   '[7.0, 1556087455006.854], [7.0, 1556087453407.881], [0.0, 1556087451385.171]]}]'
        self.assertEqual(expected, actual)
