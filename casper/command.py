from subprocess import (
    run, TimeoutExpired, CompletedProcess
)

import os
import logging


TIMEOUT_RETURN_CODE = 2
DEFAULT_TIMEOUT = 300


class StatePath(object):
    def __init__(self, path):
        self.start_dir = os.getcwd()
        self.dest_path = path

    def __enter__(self):
        os.chdir(self.dest_path)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.chdir(self.start_dir)


class TerraformCommand(object):
    def __init__(self, profile=None, timeout=DEFAULT_TIMEOUT):

        self.timeout = timeout
        env = os.environ.copy()

        # add environment variables
        if profile:
            env['AWS_PROFILE'] = profile

        self.env = env
        self.logger = logging.getLogger('casper')

    def run_command(self, terraform_command, directory="."):
        # split and run the terraform command
        cmd = terraform_command.split()
        result = self._run(cmd, directory)

        if result.returncode == TIMEOUT_RETURN_CODE:
            message = f"{directory} - Ran out of default time of " \
                      f"{self.timeout}s"
            self.logger.error(message)

            return {'success': False, 'data': message}

        if result.returncode:
            # run terraform init and try again
            init = ["terraform", "init"]
            result = self._run(init, directory)

            if not result.returncode:
                result = self._run(cmd, directory)

        if result.returncode:
            message = f"{directory} - {result.stderr.decode('utf-8')}"
            self.logger.error(message)
            return {'success': False, 'data': message}

        # process the result into a standard format
        data = result.stdout.decode('utf-8')
        return {'success': True, 'data': data}

    def _run(self, cmd, directory):
        try:
            with StatePath(directory):
                return run(
                    cmd, env=self.env, timeout=self.timeout,
                    capture_output=True
                )

        except TimeoutExpired:
            return CompletedProcess(cmd, TIMEOUT_RETURN_CODE)
