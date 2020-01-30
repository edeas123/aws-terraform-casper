from casper.state import CasperState
from casper.services.base import (
    get_service
)
import os
import logging


class Casper(object):
    def __init__(
        self,
        start_directory: str = None,
        bucket_name: str = None,
        state_file: str = "terraform_state",
        profile: str = None,
        exclude_resources: list = None,
        load_state: bool = False
    ):

        if start_directory is None or start_directory == ".":
            start_directory = os.getcwd()

        if exclude_resources is None:
            exclude_resources = []

        self.exclude_resources = exclude_resources
        self.start_dir = start_directory
        self.profile = profile

        self.bucket = bucket_name

        self.state = CasperState(
            profile=self.profile,
            bucket=self.bucket,
            state_file=state_file,
            load_state=load_state
        )
        self.logger = logging.getLogger('casper')

    def build(self, exclude_directories=None, exclude_state_res=None):
        self.logger.info("Building states...")

        return self.state.build_state_resources(
            start_dir=self.start_dir,
            exclude_directories=exclude_directories,
            exclude_state_res=exclude_state_res
        )

    def scan(self, service_name, detailed=False):

        self.logger.info(f"Scanning {service_name.upper()} service...")
        service = get_service(service_name)
        cloud_service = service(profile=self.profile)

        terraformed_resources = self.state.state_resources

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
