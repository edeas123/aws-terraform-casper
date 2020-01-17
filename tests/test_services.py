from unittest import TestCase
from unittest.mock import patch
from casper.services.ec2 import EC2Service
from casper.services.base import (
    get_supported_services, get_service, BaseService
)


class TestBaseService(TestCase):

    def test_get_service(self):
        test_service = 'ec2'
        self.assertTrue(issubclass(get_service(test_service), BaseService))
        self.assertTrue(isinstance(get_service(test_service)(), EC2Service))

    def test_get_supported_service(self):
        supported_services = get_supported_services()
        services = {'ec2', 'iam', 's3'}
        self.assertEqual(0, len(services.difference(supported_services)))

    @patch('logging.Logger.debug')
    def test_get_cloud_resources_unsupported_group(self, logger):
        ec2 = EC2Service()
        test_group = "unsupported_group"
        _ = ec2.get_cloud_resources(
            group=test_group
        )
        # logger.assert_called_once()
        logger.assert_called_with(
            f"Handler for {test_group} is not currently supported"
        )


class TestEC2Service(TestCase):

    def setUp(self) -> None:
        self.ec2 = EC2Service()

    def test_scan_service(self):
        # self.ec2.scan_service(ghosts=[])
        pass

    def test_get_cloud_resources(self):
        test_group = "aws_instance"
        # _ = self.ec2.get_cloud_resources(
        #     group=test_group
        # )
        # logger.assert_called_once()
        # logger.assert_called_with(
        #     f"Handler for {test_group} is not currently supported"
        # )
