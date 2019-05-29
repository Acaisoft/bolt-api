import unittest

from services.validators import validate_extensions


class TestExtensionsValidation(unittest.TestCase):

    def test_correct_data(self):
        ins = [
            {
                "type": "nfs",
                "extension_params": [
                    {"name": "server", "value": "1.2.3.4"},
                    {"name": "path", "value": "/bob/sinclair"},
                    {"name": "mount_options", "value": "async"},
                    {"name": "mount_options", "value": "ro"},
                ]
            }
        ]
        out = validate_extensions(ins)
        expected = [{
            'name': 'nfs',
            'server': '1.2.3.4',
            'path': '/bob/sinclair',
            'mounts_per_worker': 1,
            'mount_options': ['async', 'ro'],
        }]
        self.assertEqual(expected, out)

    def test_invalid_data(self):
        ins = [
            {
                "type": "nfs",
                "extension_params": [
                    {"name": "server", "value": "1.2.3.4"},
                    {"name": "path", "value": "/bob/sinclair"},
                    {"name": "invalid_options", "value": "invalid value"},
                ]
            }
        ]
        try:
            validate_extensions(ins)
        except AssertionError as e:
            out = str(e)
        else:
            out = 'did not raise AssertionError'
        expected = '''invalid option for "nfs": "invalid_options", valid choices are: ('server', 'path', 'mounts_per_worker', 'mount_options')'''
        self.assertEqual(expected, out)
