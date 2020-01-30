from unittest import TestCase
from moto import mock_ec2, mock_elbv2, mock_autoscaling, mock_elb
from casper.services.ec2 import EC2Service
from casper.services.base import get_service, BaseService

from tests.services.fixture import aws_credentials

import pytest
import boto3


@pytest.mark.usefixtures("aws_credentials")
class TestEC2Service(TestCase):
    def test_get_service(self):
        test_service = "ec2"
        self.assertTrue(issubclass(get_service(test_service), BaseService))
        self.assertTrue(isinstance(get_service(test_service)(), EC2Service))

    @staticmethod
    def create_subnet():
        # create the required subnets
        ec2_client = boto3.client("ec2", region_name="us-east-1")
        subnets = [
            subnet["SubnetId"] for subnet in ec2_client.describe_subnets()["Subnets"]
        ]

        return subnets

    @staticmethod
    def create_static_instances(count):
        ec2_client = boto3.client("ec2", region_name="us-east-1")
        instances = ec2_client.run_instances(
            ImageId="ami-04b9e92b5572fa0d1", MaxCount=count, MinCount=count
        )

        return instances["Instances"]

    @mock_ec2
    @mock_elbv2
    def test_get_cloud_resources_aws_alb(self):

        subnets = self.create_subnet()
        elb_client = boto3.client("elbv2", region_name="us-east-1")

        # create 200 albs
        count = 200
        for i in range(count):
            _ = elb_client.create_load_balancer(Name=f"testalb{i}", Subnets=subnets)

        # testing
        ec2 = EC2Service()
        test_group = "aws_alb"
        resources = ec2.get_cloud_resources(group=test_group)
        self.assertEqual(count, len(resources.keys()))

    @mock_ec2
    @mock_elb
    def test_get_cloud_resources_aws_elb(self):

        listeners = [
            {"Protocol": "http", "LoadBalancerPort": 80, "InstancePort": 9000},
        ]
        elb_client = boto3.client("elb", region_name="us-east-1")

        # create 200 elbs
        count = 200
        for i in range(count):
            _ = elb_client.create_load_balancer(
                LoadBalancerName=f"testelb{i}", Listeners=listeners
            )

        # testing
        ec2 = EC2Service()
        test_group = "aws_elb"
        resources = ec2.get_cloud_resources(group=test_group)

        self.assertEqual(count, len(resources.keys()))

    @mock_ec2
    def test_get_cloud_resources_aws_security_group(self):

        ec2_client = boto3.client("ec2", region_name="us-east-1")

        # create 1000 security groups
        count = 1000
        sg = []
        for i in range(count):
            sg.append(
                ec2_client.create_security_group(
                    Description=f"test sg {i}", GroupName=f"testsg{i}",
                )
            )

        # testing
        ec2 = EC2Service()
        test_group = "aws_security_group"
        resources = ec2.get_cloud_resources(group=test_group)
        self.assertEqual(
            count + 2, len(resources.keys()), "Created sg plus the two default sgs"
        )
        self.assertIn(sg[0]["GroupId"], set(resources.keys()))

    @mock_ec2
    @mock_autoscaling
    def test_get_cloud_resources_aws_instance(self):

        # setup
        ec2 = EC2Service()
        ec2_client = boto3.client("ec2", region_name="us-east-1")

        # create required subnet
        subnets = self.create_subnet()

        # launch 200 static ec2 instances
        count = 200
        instances = self.create_static_instances(count)

        # launch 300 autoscaled (dynamic) instances
        autoscaling_client = boto3.client("autoscaling", region_name="us-east-1")
        _ = autoscaling_client.create_auto_scaling_group(
            AutoScalingGroupName="autoscaler1",
            MinSize=300,
            MaxSize=300,
            VPCZoneIdentifier=subnets[0],
            InstanceId=instances[0]["InstanceId"],
        )

        # testing
        test_group = "aws_instance"
        resources = ec2.get_cloud_resources(group=test_group)

        self.assertEqual(count, len(resources.keys()))
        self.assertEqual(
            "ami-04b9e92b5572fa0d1", resources[instances[0]["InstanceId"]]["ImageId"]
        )

    @mock_ec2
    @mock_autoscaling
    def test_get_cloud_resources_aws_autoscaling_group(self):

        subnets = self.create_subnet()
        instances = self.create_static_instances(1)

        autoscaling_client = boto3.client("autoscaling", region_name="us-east-1")

        # create 300 autoscaling groups
        count = 300
        for i in range(count):
            _ = autoscaling_client.create_auto_scaling_group(
                AutoScalingGroupName=f"autoscaler{i}",
                MinSize=1,
                MaxSize=1,
                VPCZoneIdentifier=subnets[0],
                InstanceId=instances[0]["InstanceId"],
            )

        # test
        ec2 = EC2Service()
        test_group = "aws_autoscaling_group"
        resources = ec2.get_cloud_resources(group=test_group)
        self.assertEqual(count, len(resources.keys()))
