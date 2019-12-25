from subprocess import run, TimeoutExpired, CompletedProcess

import os
import logging.config
import logging

# create logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('casper')

IGNORE_PATHS = ('.git', '.terraform')
SUPPORTED_SERVICES = ('ec2', 'vpc')
DEFAULT_TIMEOUT = 300
IGNORE_RESOURCE_GROUP = ('terraform_remote_state', )
TIMEOUT_RETURN_CODE = 2


class TerraformState(object):

    def __init__(
            self, start_dir, profile=None,
            refresh_state=True, exclude_directories=None,
            bucket=None
    ):
        self.command = TerraformCommand(
            profile=profile
        )
        self.start_directory = start_dir
        self.state_resources = {}

        if refresh_state:
            if not exclude_directories:
                exclude_directories = set()
            exclude_directories.update(IGNORE_PATHS)

            for dirpath, dirnames, filenames in os.walk(start_dir):
                dirnames[:] = [
                    d for d in dirnames if d not in exclude_directories
                ]

                if self._is_terraform_state(filenames):
                    logger.info(dirpath)
                    self._list_state_resources(dirpath)
            if bucket:
                # TODO: save new state to s3 bucket
                pass

        else:
            # TODO: retrieve state from s3 bucket
            pass

    @classmethod
    def _is_terraform_state(cls, filenames):
        is_state = False
        for filename in filenames:
            if filename.endswith('.tf'):
                is_state = True
                break
        return is_state

    def _list_state_resources(self, state_directory=None):

        if state_directory is None:
            state_directory = self.start_directory

        # calls terraform state list, formats and returns a list of the result
        r = self.command.run_command(
            "terraform state list", directory=state_directory
        )
        if r['success']:
            resources = [
                resource for resource in r['data'].split('\n')
                if resource.strip()
            ]

            for resource in resources:
                resource_group = resource.split(".")[-2]

                if resource_group not in IGNORE_RESOURCE_GROUP:
                    if self.state_resources.get(resource_group, None):
                        if self.state_resources[resource_group].get(state_directory, None):
                            self.state_resources[resource_group][state_directory].append(resource)
                        else:
                            self.state_resources[resource_group][state_directory] = [resource]
                    else:
                        self.state_resources[resource_group] = {
                            state_directory: [resource]
                        }

    def get_service_resources(self, service):
        # using the resource groups, you can scan the
        # keys of state_resources and then for each state, ret
        service_resources = {}
        for resource_group in service.resources_groups.keys():
            resource_group_tag = service.resources_groups[resource_group]

            if resource_group_tag not in service_resources.keys():
                service_resources[resource_group_tag] = []

            state_path_resource = self.state_resources.get(resource_group, {})
            for state_path in state_path_resource.keys():
                for resource_identifier in state_path_resource[state_path]:
                    r = self.command.run_command(
                        f"terraform state show {resource_identifier}",
                        directory=state_path
                    )
                    if r['success']:
                        if r['data']:
                            resources = service.process_response(
                                resource_group, r['data']
                            )
                            service_resources[resource_group_tag].extend(
                                resources
                            )
                        else:
                            message = f"'{resource_identifier}' no longer " \
                                      f"exist in the state: {state_path}"
                            logger.warning(message)
                        # service_resources[resources_group].extend(res)

        return service_resources


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

    def run_command(self, terraform_command, directory="."):
        # split and run the terraform command
        cmd = terraform_command.split()
        result = self._run(cmd, directory)
        if result.returncode == TIMEOUT_RETURN_CODE:
            message = f"{directory} - Ran out of default time of " \
                      f"{self.timeout}s"
            logger.error(message)

            return {'success': False, 'data': message}

        if result.returncode:
            # run terraform init and try again
            init = ["terraform", "init"]
            result = self._run(init, directory)

            if not result.returncode:
                result = self._run(cmd, directory)

        if result.returncode:
            message = f"{directory} - {result.stderr.decode('utf-8')}"
            logger.error(message)
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
