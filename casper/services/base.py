import boto3
import os
import importlib


class BaseService(object):

    def __init__(self, profile=None):
        self._resources_groups = {}
        self.session = boto3.Session()

        if profile:
            self.session = boto3.Session(profile_name=profile)

    @property
    def resources_groups(self):
        return self._resources_groups

    def get_cloud_resources(self, group):

        # TODO: handle errors of the handler not implemented
        handler = f"_get_live_{group}"
        return getattr(self, handler)()

    def scan_service(self, ghosts):
        raise NotImplementedError


path = os.path.join(os.getcwd(), "casper", "services")
SUPPORTED_SERVICES = sorted(
    set(
        i.partition('.')[0]
        for i in os.listdir(path)
        if i.endswith(('.py', '.pyc', '.pyo'))
        and not i.startswith('__init__.py')
        and not i.startswith('base.py')
    )
)


class UnsupportedServiceException(Exception):
    pass


def get_service(service_name):
    if service_name not in SUPPORTED_SERVICES:
        raise UnsupportedServiceException()

    module = importlib.import_module(f"casper.services.{service_name}")
    service_class = f"{service_name.upper()}Service"
    service = getattr(module, service_class)

    return service
