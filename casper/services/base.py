import boto3
import importlib
import logging


SUPPORTED_SERVICES = {
    'ec2': 'EC2Service',
    'iam': 'IAMService',
    's3': 'S3Service'
}


class BaseService(object):

    def __init__(self, profile=None):
        self._resources_groups = {}
        self.session = boto3.Session()
        self.logger = logging.getLogger('casper')

        if profile:
            self.session = boto3.Session(profile_name=profile)

    @property
    def resources_groups(self):
        return self._resources_groups

    def get_cloud_resources(self, group):
        handler = getattr(self, f"_get_live_{group}", None)
        if handler:
            return handler()
        else:
            message = f"Service Handler for {group} is not currently supported"
            self.logger.debug(message)

        return None

    def scan_service(self, ghosts):
        raise NotImplementedError


class UnsupportedServiceException(Exception):
    pass


def get_service(service_name):

    module = importlib.import_module(f"casper.services.{service_name}")
    service_class = SUPPORTED_SERVICES.get(service_name, None)
    if not service_class:
        raise UnsupportedServiceException()

    service = getattr(module, service_class)

    return service
