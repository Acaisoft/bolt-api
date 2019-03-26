import json
import unittest

from schematics.exceptions import DataError

from app.validators.test_creator import validate_test_creator


class TestTestCreatorValidation(unittest.TestCase):
    @staticmethod
    def _get_fixture(fixture_path):
        file_data = json.load(open(fixture_path, 'r'))
        return json.dumps(file_data)

    def test_validate_with_wrong_data(self):
        # all fields None
        with self.assertRaises(AssertionError) as context:
            validate_test_creator(None, None, None)
        self.assertEqual(str(context.exception), 'json data is required')
        # JSON data is empty
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('', None, None)
        self.assertEqual(str(context.exception), 'json data is required')
        # wrong JSON structure
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('hello world', None, None)
        self.assertEqual(str(context.exception), 'Error during converting JSON data to python Dict')

    def test_validate_min_and_max_wait(self):
        # string min wait
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('{}', '100', 200)
        self.assertEqual(str(context.exception), 'Min wait and Max wait must be integers')
        # string max wait
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('{}', 100, '200')
        self.assertEqual(str(context.exception), 'Min wait and Max wait must be integers')
        # Max wait < Min wait
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('{}', 200, 150)
        self.assertEqual(str(context.exception), 'Max wait should be greater than Min wait')
        # Min wait < 50
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('{}', 49, 100)
        self.assertEqual(str(context.exception), 'Min wait value should be greater than or equal 50 ms')
        # Max wait < 100
        with self.assertRaises(AssertionError) as context:
            validate_test_creator('{}', 50, 99)
        self.assertEqual(str(context.exception), 'Max wait value should be greater than or equal 100 ms')

    def test_validate_json_fixtures(self):
        # good 1
        json_data = self._get_fixture('app/validators/tests/fixtures/good_1.json')
        self.assertIsNone(validate_test_creator(json_data, 100, 200))
        # good 2
        json_data = self._get_fixture('app/validators/tests/fixtures/good_2.json')
        self.assertIsNone(validate_test_creator(json_data, 100, 200))
        # good 3
        json_data = self._get_fixture('app/validators/tests/fixtures/good_3.json')
        self.assertIsNone(validate_test_creator(json_data, 100, 200))
        # bad 1
        json_data = self._get_fixture('app/validators/tests/fixtures/bad_1.json')
        with self.assertRaises(DataError) as context:
            validate_test_creator(json_data, 100, 200)
        self.assertEqual(str(context.exception), '{"test_type": ["Value must be one of (\'set\', \'sequence\')."]}')
        # bad 2
        json_data = self._get_fixture('app/validators/tests/fixtures/bad_2.json')
        with self.assertRaises(DataError) as context:
            validate_test_creator(json_data, 100, 200)
        self.assertEqual(str(context.exception), '{"payload": ["Only mappings may be used in a DictType"]}')
        # bad 3
        json_data = self._get_fixture('app/validators/tests/fixtures/bad_3.json')
        with self.assertRaises(DataError) as context:
            validate_test_creator(json_data, 100, 200)
        self.assertEqual(str(context.exception), '{"endpoints": ["This field is required."]}')
