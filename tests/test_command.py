from unittest import TestCase
from unittest.mock import Mock, patch
from casper.command import (
    TerraformCommand, DEFAULT_TIMEOUT, TIMEOUT_RETURN_CODE
)

import os


@patch("casper.command.run")
class TestTerraformCommand(TestCase):

    def setUp(self) -> None:
        self.command = TerraformCommand()

    def test_run_command_working(self, mock_run):
        mock_run.return_value = Mock(
            returncode=0, stdout=b'working', stderr=b''
        )
        result = self.command.run_command("dummy command")

        mock_run.assert_called_once()
        mock_run.assert_called_with(
            ['dummy', 'command'],
            capture_output=True,
            env=os.environ.copy(),
            timeout=DEFAULT_TIMEOUT
        )
        self.assertEqual(
            {'success': True, 'data': 'working'},
            result
        )

    def test_run_command_timeout(self, mock_run):
        mock_run.return_value = Mock(
            returncode=TIMEOUT_RETURN_CODE, stdout=b'', stderr=b'timeout'
        )
        result = self.command.run_command(
            "dummy command", directory=os.getcwd()
        )
        mock_run.assert_called_once()
        self.assertEqual(
            {
                'success': False,
                'data': f'{os.getcwd()} - Ran out of '
                        f'default time of {DEFAULT_TIMEOUT}s'
            },
            result
        )

    def test_run_command_failed(self, mock_run):
        mock_run.return_value = Mock(
            returncode=1, stdout=b'', stderr=b'failing'
        )
        result = self.command.run_command(
            "dummy command", directory=os.getcwd()
        )
        self.assertEqual(2, mock_run.call_count)
        self.assertEqual(
            {
                'success': False,
                'data': f'{os.getcwd()} - failing'
            },
            result
        )

