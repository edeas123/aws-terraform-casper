import boto3
import importlib
import logging

from abc import ABC, abstractmethod

SUPPORTED_SERVICES = {"ec2": "EC2Service", "iam": "IAMService", "s3": "S3Service"}


class BaseService(ABC):
    def __init__(self, profile=None):
        self._resources_groups = {}
        self.session = boto3.Session()
        self.logger = logging.getLogger("casper")

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

    @abstractmethod
    def scan_service(self, ghosts):
        pass


class UnsupportedServiceException(Exception):
    pass


def get_service(service_name):

    if service_name not in SUPPORTED_SERVICES:
        raise UnsupportedServiceException()

    module = importlib.import_module(f"casper.services.{service_name}")
    service_class = SUPPORTED_SERVICES.get(service_name, None)
    service = getattr(module, service_class)

    return service
