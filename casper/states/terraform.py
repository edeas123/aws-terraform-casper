import os
import logging

from casper.command import TerraformCommand


IGNORE_PATHS = ('.git', '.terraform')
IGNORE_RESOURCE_GROUP = ('terraform_remote_state', )


class TerraformState(object):

    def __init__(
        self,
        profile=None,
        bucket=None,
        load_state=False
    ):
        self.profile = profile
        self.bucket = bucket

        self.command = TerraformCommand(
            profile=self.profile
        )

        if load_state:
            self._load_state()
        else:
            self.state_resources = {}

        self._exclude_state_res = set()
        self._counter = {
            'state': 0,
            'resource': 0,
            'resource_group': 0,
        }
        self.logger = logging.getLogger('casper')

    def build_state_resources(
        self,
        start_dir=".",
        exclude_directories=None,
        exclude_state_res=None
    ):

        if not exclude_directories:
            exclude_directories = set()

        if not exclude_state_res:
            exclude_state_res = set()

        exclude_directories.update(IGNORE_PATHS)
        exclude_state_res.update(IGNORE_RESOURCE_GROUP)
        self._exclude_state_res = exclude_state_res

        for dirpath, dirnames, filenames in os.walk(start_dir):
            dirnames[:] = [
                d for d in dirnames if d not in exclude_directories
            ]

            if self._is_terraform_state(filenames):
                self.logger.debug(f"In {dirpath}")
                self._list_state_resources(dirpath)

        # save state
        self._save_state()

        return self._counter

    def _save_state(self):
        raise NotImplementedError

    def _load_state(self):
        raise NotImplementedError

    def _list_state_resources(
        self, state_directory=None
    ):

        # calls terraform state list, formats and returns a list of the result
        r = self.command.run_command(
            "terraform state list", directory=state_directory
        )
        if r['success']:
            self._counter['state'] += 1
            resources = [
                resource
                for resource in r['data'].split('\n')
                if resource.strip()
            ]

            for resource in resources:
                resource_group = resource.split(".")[-2]
                if resource_group not in self._exclude_state_res:
                    resource_id = self._get_state_resource(
                        state_directory, resource
                    )
                    if resource_id:
                        self._counter['resource'] += 1
                        resource_group_tag = self._resource_group_remap.get(
                            resource_group, resource_group
                        )

                        if self.state_resources.get(resource_group_tag, None):
                            self.state_resources[resource_group_tag].append(
                                resource_id
                            )
                        else:
                            self._counter['resource_group'] += 1
                            self.state_resources[resource_group_tag] = (
                                [resource_id]
                            )

    def _get_state_resource(self, directory, resource_identifier):

        resource_id = None
        resource_group = resource_identifier.split(".")[-2]
        r = self.command.run_command(
            f"terraform state show {resource_identifier}",
            directory=directory
        )
        if r['success']:
            if r['data']:
                resource_id = self._process_response(
                    resource_group, r['data']
                )
            else:
                message = f"'{resource_identifier}' no longer " \
                          f"exist in the state: {directory}"
                self.logger.warning(message)

        return resource_id

    def _process_response(self, group, text):
        handler = getattr(self, f"_get_state_{group}", None)
        if handler:
            return handler(text)
        else:
            message = f"State Handler for {group} is not currently supported"
            self.logger.debug(message)
            self._exclude_state_res.add(group)

        return None

    @classmethod
    def _is_terraform_state(cls, filenames):
        is_state = False
        for filename in filenames:
            if filename.endswith('.tf'):
                is_state = True
                break
        return is_state
