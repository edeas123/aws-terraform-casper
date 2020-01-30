from unittest import TestCase
from moto import mock_s3
from casper.services.s3 import S3Service
from casper.services.base import get_service, BaseService
from tests.services.fixture import aws_credentials

import boto3
import pytest


@pytest.mark.usefixtures("aws_credentials")
class TestS3Service(TestCase):
    def test_get_service(self):
        test_service = "s3"
        self.assertTrue(issubclass(get_service(test_service), BaseService))
        self.assertTrue(isinstance(get_service(test_service)(), S3Service))

    @mock_s3
    def test_get_cloud_resources_aws_s3_bucket(self):
        s3 = S3Service()
        conn = boto3.resource("s3")

        # create 300 buckets
        count = 300
        for i in range(count):
            _ = conn.create_bucket(Bucket=f"testbucket{i}")

        test_group = "aws_s3_bucket"
        resources = s3.get_cloud_resources(group=test_group)
        self.assertEqual(count, len(resources.keys()))
        self.assertEqual(
            ["Name", "CreationDate"], list(resources["testbucket0"].keys())
        )
