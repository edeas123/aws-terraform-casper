from services.base import BaseService

import boto3


class EC2Service(BaseService):

    def __init__(self, vendor: str, profile: str = None):

        super().__init__(profile=profile)
        if vendor == "terraform":
            self._resources_groups = {
                'aws_instance': 'Instance',
                'aws_autoscaling_group': 'AutoScalingGroup',
                'aws_spot_instance_request': 'Instance',
                'aws_security_group': 'SecurityGroup',
            }
        elif vendor == "aws":
            self._resources_groups = {
                'aws_instance': 'Instance',
                'aws_autoscaling_group': 'AutoScalingGroup',
                'aws_security_group': 'SecurityGroup',
            }

    def _get_live_aws_instance(self):

        ec2_client = self.session.client('ec2')
        ec2 = ec2_client.describe_instances()
        instances = [
            reservation['Instances']
            for reservation in ec2['Reservations']
        ]
        instances_id = [
            instance['InstanceId'] for instance_group in instances
            for instance in instance_group if instance['State']['Code'] == 16
        ]

        # TODO: find better way of doing thing
        # remove dynamic instances
        asg_client = boto3.client('autoscaling')
        asgs = asg_client.describe_auto_scaling_instances()

        dynamic_instances = [
            instance['InstanceId'] for instance in asgs['AutoScalingInstances']
        ]
        while 'NextToken' in asgs.keys():
            asgs = asg_client.describe_auto_scaling_instances(
                NextToken=asgs['NextToken']
            )
            dynamic_instances.extend(
                instance['InstanceId'] for instance in asgs['AutoScalingInstances']
            )

        return set(instances_id).difference(set(dynamic_instances))

    def _get_live_aws_autoscaling_group(self):

        asg_client = self.session.client('autoscaling')
        asgs = asg_client.describe_auto_scaling_groups()
        asgs_names = [
            a['AutoScalingGroupName'] for a in asgs['AutoScalingGroups']
        ]

        while 'NextToken' in asgs.keys():
            asgs = asg_client.describe_auto_scaling_groups(
                NextToken=asgs['NextToken']
            )
            asgs_names.extend([
                a['AutoScalingGroupName'] for a in asgs['AutoScalingGroups']
            ])

        return asgs_names

    def _get_live_aws_security_group(self):
        ec2_client = self.session.client('ec2')

        sgs = ec2_client.describe_security_groups()
        sg_ids = [sg['GroupId'] for sg in sgs['SecurityGroups']]

        while 'NextToken' in sgs.keys():
            sgs = ec2_client.describe_security_groups(
                NextToken=sgs['NextToken']
            )
            sg_ids.extend(
                [sg['GroupId'] for sg in sgs['SecurityGroups']]
            )

        return sg_ids

    def _get_state_aws_instance(self, text):
        return [self._get_field('id', text)]

    def _get_state_aws_autoscaling_group(self, text):
        return [self._get_field('id', text)]

    def _get_state_aws_spot_instance_request(self, text):
        return [self._get_field('spot_instance_id', text)]

    def _get_state_aws_security_group(self, text):
        return [self._get_field('id', text)]

    def scan_service(self, ghosts):
        if len(ghosts['AutoScalingGroup']['ids']) > 0:
            # get the instances in defaulting asg and add it to the
            # overall defaulting instances

            defaulting_asgs = ghosts['AutoScalingGroup']['ids']
            asg_client = self.session.client('autoscaling')
            asgs = asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=defaulting_asgs
            )
            instances = [
                instance['InstanceId'] for sublist in (
                    afull['Instances'] for afull in asgs['AutoScalingGroups']
                ) for instance in sublist
            ]

            while 'NextToken' in asgs.keys():
                asgs = asg_client.describe_auto_scaling_groups(
                    AutoScalingGroupNames=defaulting_asgs
                )
                instances.extend([
                    instance['InstanceId'] for sublist in (
                        afull['Instances'] for afull in asgs['AutoScalingGroups']
                    ) for instance in sublist
                ])

            ghosts['Instance']['ids'].extend(instances)
            ghosts['Instance']['count'] = len(
                ghosts['Instance']['ids']
            )
