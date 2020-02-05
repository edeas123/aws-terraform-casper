import boto3
import importlib
import logging
import pkgutil
import os
import re
import casper.services

from abc import ABC, abstractmethod


def get_supported_services():
    pkgpath = os.path.dirname(casper.services.__file__)
    supported_services = [
        name for _, name, _ in pkgutil.iter_modules([pkgpath]) if name != "base"
    ]
    return supported_services


def get_service(service_name):

    if service_name not in get_supported_services():
        raise UnsupportedServiceException()

    module = importlib.import_module(f"casper.services.{service_name}")
    service_class = f"{service_name.upper()}Service"
    service = getattr(module, service_class, None)

    return service


class ResourceGroupManager:
    @classmethod
    def _class_from_group(cls, group):
        group_fmt = group.title().replace("_", "")
        class_name = f"{group_fmt}Resource"
        supported_services = get_supported_services()

        for service_name in supported_services:
            module = importlib.import_module(f"casper.services.{service_name}")
            resource_class = getattr(module, class_name, None)

            if resource_class:
                return resource_class

        return None

    @classmethod
    def get_resource_handler(cls, group):
        return cls._class_from_group(group)

    @classmethod
    def get_tag(cls, group):
        resource_class = cls._class_from_group(group)
        return resource_class.get_tag()


class Resource(ABC):
    def __init__(self):
        self.session = boto3.Session()

    def get_state_resource(self, text):
        return self._get_field("id", text)

    @staticmethod
    def _get_field(field, resource):
        pattern = f"(\\n|^|\\n\\s+)({field}\\s+.*?)(\\n)"
        resource = resource.replace("\x1b[1m\x1b[0m", "").replace("\x1b[0m\x1b[0m", "")
        match = re.search(pattern, resource)[0]
        value = match.split("=")[1].strip(' "\n')
        return value

    @classmethod
    def get_tag(cls):
        return cls._tag

    @property
    @abstractmethod
    def _tag(self):
        pass


class Service:
    def __init__(self, profile=None):
        self._resources_groups = {}
        self.session = boto3.Session()
        self.logger = logging.getLogger("casper")
        self.resources_group_manager = ResourceGroupManager()

        if profile:
            self.session = boto3.Session(profile_name=profile)

    @property
    def resources_groups(self):
        return self._resources_groups

    def get_cloud_resources(self, group):
        handler = self.resources_group_manager.get_resource_handler(group)
        if handler:
            return handler().get_cloud_resource()
        else:
            message = f"Service Handler for {group} is not currently supported"
            self.logger.debug(message)

        return None

    def scan_service(self, ghosts):
        pass


class UnsupportedServiceException(Exception):
    pass
