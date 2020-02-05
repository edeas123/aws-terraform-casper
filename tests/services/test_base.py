from unittest import TestCase
from unittest.mock import patch
from casper.services.ec2 import EC2Service
from casper.services import (
    get_service,
    UnsupportedServiceException,
    get_supported_services,
    Service
)


class TestService(TestCase):
    def setUp(self) -> None:
        self.ec2 = EC2Service()

    @patch("logging.Logger.debug")
    def test_get_cloud_resources_unsupported_group(self, logger):
        test_group = "unsupported_group"
        handler = self.ec2.get_cloud_resources(group=test_group)
        logger.assert_called_once()
        logger.assert_called_with(
            f"Service Handler for {test_group} is not currently supported"
        )
        self.assertIsNone(handler)

    def test_get_unsupported_service(self):
        service_name = "unsupported_service"
        self.assertRaises(UnsupportedServiceException, get_service, service_name)

    def test_get_all_supported_service(self):
        for svc in get_supported_services():
            service = get_service(svc)
            self.assertTrue(issubclass(service, Service))
            self.assertIsNotNone(service)

