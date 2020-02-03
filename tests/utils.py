import os
import pytest
import boto3


@pytest.fixture(scope="class")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def create_subnet():
    # create the required subnets
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    subnets = [
        subnet["SubnetId"] for subnet in ec2_client.describe_subnets()["Subnets"]
    ]

    return subnets


def create_static_instances(count):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    instances = ec2_client.run_instances(
        ImageId="ami-04b9e92b5572fa0d1", MaxCount=count, MinCount=count
    )

    return instances["Instances"]


def create_autoscaling_group(name, instance_id, subnet, count):
    autoscaling_client = boto3.client("autoscaling", region_name="us-east-1")
    _ = autoscaling_client.create_auto_scaling_group(
        AutoScalingGroupName=name,
        MinSize=count,
        MaxSize=count,
        VPCZoneIdentifier=subnet,
        InstanceId=instance_id,
    )


def load_sample(filename):
    filepath = os.path.join(os.getcwd(), "tests", "samples", filename)
    with open(filepath, "r") as fid:
        sample = fid.read()

    return sample
