from unittest import TestCase
from moto import mock_iam
from casper.services.iam import IAMService
from casper.services.base import get_service, BaseService

from tests.services.fixture import aws_credentials

import boto3
import json
import pytest


@mock_iam
@pytest.mark.usefixtures("aws_credentials")
class TestIAMService(TestCase):
    def setUp(self) -> None:
        self.iam = IAMService()
        self.conn = boto3.resource("iam")

    def test_get_service(self):
        test_service = "iam"
        self.assertTrue(issubclass(get_service(test_service), BaseService))
        self.assertTrue(isinstance(get_service(test_service)(), IAMService))

    def test_get_cloud_resources_aws_iam_user(self):

        # create 1000 users
        count = 1000
        for i in range(count):
            _ = self.conn.create_user(UserName=f"testuser{i}")

        test_group = "aws_iam_user"
        resources = self.iam.get_cloud_resources(group=test_group)
        self.assertEqual(count, len(resources.keys()))
        self.assertEqual(
            ["Path", "UserName", "UserId", "Arn", "CreateDate"],
            list(resources["testuser0"].keys()),
        )

    def test_get_cloud_resources_aws_iam_role(self):

        policy_docs = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Effect": "Allow",
                        "Sid": "",
                    }
                ],
            }
        )

        # create 500 roles
        count = 500
        for i in range(count):
            self.conn.create_role(
                RoleName=f"testrole{i}", AssumeRolePolicyDocument=policy_docs
            )

        test_group = "aws_iam_role"
        resources = self.iam.get_cloud_resources(group=test_group)
        self.assertEqual(count, len(resources.keys()))
        self.assertEqual(
            [
                "Path",
                "RoleName",
                "RoleId",
                "Arn",
                "CreateDate",
                "AssumeRolePolicyDocument",
            ],
            list(resources["testrole0"].keys()),
        )
