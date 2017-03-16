import sys
from unittest import TestCase
from economicpy.config_check import ConfigCheck
from contextlib import contextmanager
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestConfigCheck(TestCase):
    def test_make_list(self):
        tuple_list = [(1, 2), (3, 4), (5, 6)]
        output = ConfigCheck.make_list(tuple_list)
        self.assertEqual(output, [1, 3, 5])

    def test_raises_exception_for_non_existing_config_file(self):
        with self.assertRaises(Exception):
            ConfigCheck('non_existing_config_file', 'non_existing_reference_config_file')

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.isfile', return_value=True)
    def test_does_not_raise_exception_for_existing_config_file(self, *args):
        ConfigCheck('non_existing_config_file', 'non_existing_reference_config_file')

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.isfile', return_value=True)
    def test_find_missing_setting(self, *args):
        config = ConfigCheck('non_existing_config_file', 'non_existing_reference_config_file')
        dist_items = [('key1', 'value1'), ('key2', 'value2')]
        ini_items = [('key1', 'value1')]

        with captured_output() as (out, err):
            config.find_differences(dist_items=dist_items, ini_items=ini_items)
        output = out.getvalue().strip()
        self.assertEqual(output, 'Missing settings: key2')

    @patch('os.path.isdir', return_value=True)
    @patch('os.path.isfile', return_value=True)
    def test_find_not_needed_setting(self, *args):
        config = ConfigCheck('non_existing_config_file', 'non_existing_reference_config_file')
        dist_items = [('key1', 'value1')]
        ini_items = [('key1', 'value1'), ('key2', 'value2')]

        with captured_output() as (out, err):
            config.find_differences(dist_items=dist_items, ini_items=ini_items)
        output = out.getvalue().strip()
        self.assertEqual(output, 'Not needed settings: key2')
