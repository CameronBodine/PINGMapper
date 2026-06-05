"""Unit tests for CLI dispatch and self-check behavior."""

import importlib
import sys
import types
import unittest
from unittest import mock


class TestCliDispatch(unittest.TestCase):
    """Validate command dispatch logic in pingmapper.__main__."""

    def test_main_check_dispatches_to_self_check(self):
        cli = importlib.import_module('pingmapper.__main__')

        fake_mod = types.ModuleType('pingmapper.self_check')
        fake_run = mock.Mock(return_value=7)
        fake_mod.run_self_check = fake_run

        with mock.patch.dict(sys.modules, {'pingmapper.self_check': fake_mod}):
            result = cli.main('check')

        self.assertEqual(result, 7)
        fake_run.assert_called_once_with(verbose=True)

    def test_main_test_unit_dispatches_to_self_check(self):
        cli = importlib.import_module('pingmapper.__main__')

        fake_mod = types.ModuleType('pingmapper.self_check')
        fake_run = mock.Mock(return_value=3)
        fake_mod.run_self_check = fake_run

        with mock.patch.dict(sys.modules, {'pingmapper.self_check': fake_mod}):
            result = cli.main('test_unit')

        self.assertEqual(result, 3)
        fake_run.assert_called_once_with(verbose=True)

    def test_main_unknown_process_returns_zero(self):
        cli = importlib.import_module('pingmapper.__main__')
        self.assertEqual(cli.main('not-a-command'), 0)

    def test_module_sets_default_process_to_gui_when_no_args(self):
        cli = importlib.import_module('pingmapper.__main__')

        with mock.patch.object(sys, 'argv', ['python']):
            cli = importlib.reload(cli)
            self.assertEqual(cli.to_do, 'gui')

    def test_module_uses_first_arg_as_process(self):
        cli = importlib.import_module('pingmapper.__main__')

        with mock.patch.object(sys, 'argv', ['python', 'check']):
            cli = importlib.reload(cli)
            self.assertEqual(cli.to_do, 'check')


class TestSelfCheck(unittest.TestCase):
    """Validate dependency-check and test-run exit code behavior."""

    def test_missing_required_modules_collects_only_failures(self):
        self_check = importlib.import_module('pingmapper.self_check')

        def _fake_import(name):
            if name in {'numpy', 'pingwizard'}:
                raise ImportError('missing')
            return object()

        with mock.patch.object(self_check.importlib, 'import_module', side_effect=_fake_import):
            missing = self_check._missing_required_modules()

        self.assertEqual(missing, ['numpy', 'pingwizard'])

    def test_run_self_check_returns_1_when_dependencies_missing(self):
        self_check = importlib.import_module('pingmapper.self_check')

        with mock.patch.object(self_check, '_missing_required_modules', return_value=['numpy']):
            code = self_check.run_self_check(verbose=False)

        self.assertEqual(code, 1)

    def test_run_self_check_returns_1_when_tests_fail(self):
        self_check = importlib.import_module('pingmapper.self_check')

        fake_suite = object()
        fake_result = types.SimpleNamespace(wasSuccessful=lambda: False)
        fake_runner = mock.Mock()
        fake_runner.run.return_value = fake_result

        with mock.patch.object(self_check, '_missing_required_modules', return_value=[]), \
             mock.patch.object(self_check.unittest.defaultTestLoader, 'loadTestsFromNames', return_value=fake_suite) as load_mock, \
             mock.patch.object(self_check.unittest, 'TextTestRunner', return_value=fake_runner):
            code = self_check.run_self_check(verbose=False)

        self.assertEqual(code, 1)
        load_mock.assert_called_once_with(self_check.UNIT_TEST_MODULES)
        fake_runner.run.assert_called_once_with(fake_suite)

    def test_run_self_check_returns_0_when_tests_pass(self):
        self_check = importlib.import_module('pingmapper.self_check')

        fake_suite = object()
        fake_result = types.SimpleNamespace(wasSuccessful=lambda: True)
        fake_runner = mock.Mock()
        fake_runner.run.return_value = fake_result

        with mock.patch.object(self_check, '_missing_required_modules', return_value=[]), \
             mock.patch.object(self_check.unittest.defaultTestLoader, 'loadTestsFromNames', return_value=fake_suite) as load_mock, \
             mock.patch.object(self_check.unittest, 'TextTestRunner', return_value=fake_runner):
            code = self_check.run_self_check(verbose=False)

        self.assertEqual(code, 0)
        load_mock.assert_called_once_with(self_check.UNIT_TEST_MODULES)
        fake_runner.run.assert_called_once_with(fake_suite)


if __name__ == '__main__':
    unittest.main()
