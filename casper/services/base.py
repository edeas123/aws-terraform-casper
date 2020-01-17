import boto3
import os
import importlib
import logging

from abc import ABC, abstractmethod

logger = logging.getLogger('casper')


class BaseService(ABC):

    def __init__(self, profile=None):
        self._resources_groups = {}
        self.session = boto3.Session()

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
            print("here")
            message = f"Handler for {group} is not currently supported"
            logging.debug(message)

        return None

    @abstractmethod
    def scan_service(self, ghosts):
        pass


class UnsupportedServiceException(Exception):
    pass


def get_supported_services():
    path = os.path.join(os.getcwd(), "casper", "services")
    supported_services = sorted(
        set(
            i.partition('.')[0]
            for i in os.listdir(path)
            if i.endswith(('.py', '.pyc', '.pyo'))
            and not i.startswith('__init__.py')
            and not i.startswith('base.py')
        )
    )

    return supported_services


def get_service(service_name):
    if service_name not in get_supported_services():
        raise UnsupportedServiceException()

    module = importlib.import_module(f"casper.services.{service_name}")
    service_class = f"{service_name.upper()}Service"
    service = getattr(module, service_class)

    return service
