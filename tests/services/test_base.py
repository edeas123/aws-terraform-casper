from unittest import TestCase
from unittest.mock import patch
from casper.services.ec2 import EC2Service


class TestBaseService(TestCase):

    def setUp(self) -> None:
        self.ec2 = EC2Service()

    @patch('logging.Logger.debug')
    def test_get_cloud_resources_unsupported_group(self, logger):
        test_group = "unsupported_group"
        handler = self.ec2.get_cloud_resources(
            group=test_group
        )
        logger.assert_called_once()
        logger.assert_called_with(
            f"Service Handler for {test_group} is not currently supported"
        )
        self.assertIsNone(handler)
