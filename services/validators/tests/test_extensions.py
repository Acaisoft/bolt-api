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
        expected = [{'type': 'nfs', 'server': '1.2.3.4', 'path': '/bob/sinclair', 'mount_options': ['async', 'ro']}]
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
        out = validate_extensions(ins)
        expected = [{'type': 'nfs', 'server': '1.2.3.4', 'path': '/bob/sinclair', 'mount_options': []}]
        self.assertEqual(expected, out)
