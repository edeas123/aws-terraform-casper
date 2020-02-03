from unittest import TestCase
from unittest.mock import patch
from casper import Casper
from casper import CasperState

from casper.services.base import SUPPORTED_SERVICES
from tests.utils import (
    aws_credentials,
    create_subnet,
    create_static_instances,
    create_autoscaling_group,
)
from moto import mock_ec2, mock_elbv2, mock_autoscaling, mock_elb, mock_iam, mock_s3

import os
import boto3
import pytest


@mock_s3
@mock_iam
@mock_elb
@mock_elbv2
@mock_autoscaling
@mock_ec2
@pytest.mark.usefixtures("aws_credentials")
class TestCasper(TestCase):
    @patch.object(CasperState, "build_state_resources")
    def test_casper_build(self, mock_build):
        casper = Casper()
        casper.build(exclude_directories={"test"}, exclude_state_res={"test_res"})

        mock_build.assert_called_with(
            exclude_directories={"test"},
            exclude_state_res={"test_res"},
            start_dir=os.getcwd(),
        )

    @patch("casper.CasperState")
    def test_casper_scan(self, MockCasperState):
        mock_casper_state = MockCasperState()

        # create required subnet
        subnets = create_subnet()

        # launch 200 static ec2 instances
        count = 2
        instances = create_static_instances(count)

        # launch 3 autoscaled (dynamic) instances
        create_autoscaling_group(
            name="autoscaler1",
            instance_id=instances[0]["InstanceId"],
            subnet=subnets[0],
            count=3,
        )

        # get the default sg which will show up asa ghosts
        ec2_client = boto3.client("ec2", region_name="us-east-1")
        sgs = ec2_client.describe_security_groups()

        ec2 = ec2_client.describe_instances()
        reservations = [reservation["Instances"] for reservation in ec2["Reservations"]]

        casper = Casper()
        casper.casper_state = mock_casper_state
        mock_casper_state.state_resources = {}

        aws_instance = [
            instance["InstanceId"]
            for instance_group in reservations
            for instance in instance_group
            if instance["State"]["Code"] == 16
        ]
        aws_security_group = [sg["GroupId"] for sg in sgs["SecurityGroups"]]
        aws_alb = []
        aws_elb = []

        expected_ghosts = {
            "ec2": {
                "aws_instance": {"ids": aws_instance, "count": 5},
                "aws_autoscaling_group": {"ids": ["autoscaler1"], "count": 1},
                "aws_security_group": {"ids": aws_security_group, "count": 2},
                "aws_alb": {"ids": aws_alb, "count": 0},
                "aws_elb": {"ids": aws_elb, "count": 0},
            },
            "s3": {"aws_s3_bucket": {"count": 0, "ids": []}},
            "iam": {
                "aws_iam_role": {"count": 0, "ids": []},
                "aws_iam_user": {"count": 0, "ids": []},
            },
        }

        for svc in SUPPORTED_SERVICES:
            ghosts = casper.scan(svc)
            for keys in ghosts:
                self.assertEqual(
                    expected_ghosts[svc][keys]["count"], ghosts[keys]["count"]
                )
                self.assertSetEqual(
                    set(expected_ghosts[svc][keys]["ids"]), set(ghosts[keys]["ids"])
                )

        mock_casper_state.load_state.assert_not_called()

    @patch("casper.CasperState")
    def test_casper_scan_with_detailed(self, MockCasperState):
        mock_casper_state = MockCasperState()

        # create required subnet
        subnets = create_subnet()

        # launch 200 static ec2 instances
        count = 2
        instances = create_static_instances(count)

        # launch 3 autoscaled (dynamic) instances
        create_autoscaling_group(
            name="autoscaler1",
            instance_id=instances[0]["InstanceId"],
            subnet=subnets[0],
            count=3,
        )

        casper = Casper()
        casper.casper_state = mock_casper_state
        mock_casper_state.state_resources = {}

        for svc in SUPPORTED_SERVICES:
            ghosts = casper.scan(svc, detailed=True)
            print(ghosts)
            for resource_group in ghosts:
                self.assertTrue("resources" in ghosts[resource_group])

        mock_casper_state.load_state.assert_not_called()
