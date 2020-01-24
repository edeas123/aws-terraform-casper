from casper.states.aws import AWSState
from casper.services.base import (
    get_service
)
import os


class Casper(object):
    def __init__(
        self,
        bucket_name: str = "",
        start_directory: str = None,
        state_file: str = "terraform_state",
        profile: str = None,
        exclude_resources: set = None,
        load_state: bool = False
    ):

        if start_directory is None or start_directory == ".":
            start_directory = os.getcwd()

        if exclude_resources is None:
            exclude_resources = set()

        self.exclude_resources = exclude_resources
        self.start_dir = start_directory
        self.profile = profile

        self.bucket = bucket_name

        self.tf = AWSState(
            profile=self.profile,
            bucket=self.bucket,
            state_file=state_file,
            load_state=load_state
        )

    def build(self, exclude_directories=None, exclude_state_res=None):
        return self.tf.build_state_resources(
            start_dir=self.start_dir,
            exclude_directories=exclude_directories,
            exclude_state_res=exclude_state_res
        )

    def scan(self, service_name, detailed=False):

        service = get_service(service_name)
        cloud_service = service(profile=self.profile)

        terraformed_resources = self.tf.state_resources

        ghosts = {}
        for resource_group in cloud_service.resources_groups:
            resources = cloud_service.get_cloud_resources(resource_group)
            diff = set(resources.keys()).difference(
                set(terraformed_resources.get(resource_group, []))
            )
            ghosts[resource_group] = {}
            ghosts[resource_group]['ids'] = [
                d for d in diff if d not in self.exclude_resources
            ]
            ghosts[resource_group]['count'] = len(
                ghosts[resource_group]['ids']
            )

            if detailed:
                ghosts[resource_group]['resources'] = [
                    resources[d] for d in diff
                    if d not in self.exclude_resources
                ]

        cloud_service.scan_service(ghosts)

        return ghosts
