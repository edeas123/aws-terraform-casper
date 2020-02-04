import re
import boto3
import sys

from abc import ABC, abstractmethod


class ResourceGroupManager:

    @classmethod
    def _class_from_group(cls, group):
        group_fmt = group.title().replace("_", "")
        class_name = f"{group_fmt}Resource"

        resource_class = getattr(sys.modules[__name__], class_name, None)
        return resource_class

    @classmethod
    def get_resource_handler(cls, group):
        return cls._class_from_group(group)

    @classmethod
    def get_name(cls, group):
        resource_class = cls._class_from_group(group)
        return resource_class.get_name()


class Resource(ABC):

    def __init__(self):
        self.session = boto3.Session()

    def get_state_resource(self, text):
        return self._get_field("id", text)

    @staticmethod
    def _get_field(field, resource):
        pattern = f"(\\n|^)({field}\\s+.*?)(\\n)"
        match = re.search(pattern, resource)[0]
        value = match.split("=")[1].strip()
        return value

    @classmethod
    def get_name(cls):
        return cls._name

    @property
    @abstractmethod
    def _name(self):
        pass


class AwsAlbResource(Resource):

    _name = "aws_alb"

    def get_state_resource(self, text):
        return self._get_field("name", text)

    def get_cloud_resource(self):
        alb_client = self.session.client("elbv2")
        alb = alb_client.describe_load_balancers()
        lbs = {lb["LoadBalancerName"]: lb for lb in alb["LoadBalancers"]}

        while "NextMarker" in alb.keys():
            alb = alb_client.describe_load_balancers(Marker=alb["NextMarker"])
            lbs.update({lb["LoadBalancerName"]: lb for lb in alb["LoadBalancers"]})

        return lbs


class AwsLbResource(AwsAlbResource):
    pass


class AwsInstanceResource(Resource):

    _name = "aws_instance"

    def get_cloud_resource(self):

        ec2_client = self.session.client("ec2")
        ec2 = ec2_client.describe_instances()
        instances = [reservation["Instances"] for reservation in ec2["Reservations"]]
        ec2s = {
            instance["InstanceId"]: instance
            for instance_group in instances
            for instance in instance_group
            if instance["State"]["Code"] == 16
        }

        # TODO: find better way of doing thing
        # remove dynamic instances
        asg_client = self.session.client("autoscaling")
        asgs = asg_client.describe_auto_scaling_instances()

        dynamic_instances = [
            instance["InstanceId"] for instance in asgs["AutoScalingInstances"]
        ]
        while "NextToken" in asgs.keys():
            asgs = asg_client.describe_auto_scaling_instances(
                NextToken=asgs["NextToken"]
            )
            dynamic_instances.extend(
                instance["InstanceId"] for instance in asgs["AutoScalingInstances"]
            )

        static_instances = {
            k: ec2s[k] for k in set(ec2s.keys()).difference(set(dynamic_instances))
        }

        return static_instances


class AwsSpotInstanceRequestResource(AwsInstanceResource):

    _name = "aws_instance"

    def get_state_resource(self, text):
        return self._get_field("spot_instance_id", text)


class AwsElbResource(Resource):

    _name = "aws_elb"

    def get_state_resource(self, text):
        return self._get_field("name", text)

    def get_cloud_resource(self):
        elb_client = self.session.client("elb")
        elb = elb_client.describe_load_balancers()
        lbs = {lb["LoadBalancerName"]: lb for lb in elb["LoadBalancerDescriptions"]}

        while "NextMarker" in elb.keys():
            elb = elb_client.describe_load_balancers(Marker=elb["NextMarker"])
            lbs.update(
                {lb["LoadBalancerName"]: lb for lb in elb["LoadBalancerDescriptions"]}
            )

        return lbs


class AwsAutoscalingGroupResource(Resource):

    _name = "aws_autoscaling_group"

    def get_state_resource(self, text):
        return self._get_field("name", text)

    def get_cloud_resource(self):
        asg_client = self.session.client("autoscaling")
        asgs_group = asg_client.describe_auto_scaling_groups()
        asgs = {a["AutoScalingGroupName"]: a for a in asgs_group["AutoScalingGroups"]}

        while "NextToken" in asgs_group.keys():
            asgs_group = asg_client.describe_auto_scaling_groups(
                NextToken=asgs_group["NextToken"]
            )
            asgs.update(
                {a["AutoScalingGroupName"]: a for a in asgs_group["AutoScalingGroups"]}
            )

        return asgs


class AwsSecurityGroupResource(Resource):

    _name = "aws_security_group"

    def get_cloud_resource(self):
        ec2_client = self.session.client("ec2")

        sgs_group = ec2_client.describe_security_groups()
        sgs = {sg["GroupId"]: sg for sg in sgs_group["SecurityGroups"]}

        while "NextToken" in sgs_group.keys():
            sgs_group = ec2_client.describe_security_groups(
                NextToken=sgs_group["NextToken"]
            )
            sgs.update({sg["GroupId"]: sg for sg in sgs_group["SecurityGroups"]})

        return sgs


class AwsS3BucketResource(Resource):

    _name = "aws_s3"

    def get_cloud_resource(self):
        s3_client = self.session.client("s3")
        s3_buckets = s3_client.list_buckets()
        buckets = {bucket["Name"]: bucket for bucket in s3_buckets["Buckets"]}

        return buckets


class AwsIamUserResource(Resource):

    _name = "aws_iam_user"

    def get_cloud_resource(self):
        iam_client = self.session.client("iam")
        iam_users = iam_client.list_users()
        users = {user["UserName"]: user for user in iam_users["Users"]}

        return users


class AwsIamRoleResource(Resource):

    _name = "aws_iam_role"

    def get_cloud_resource(self):
        iam_client = self.session.client("iam")
        iam_roles = iam_client.list_roles()
        roles = {role["RoleName"]: role for role in iam_roles["Roles"]}

        return roles
