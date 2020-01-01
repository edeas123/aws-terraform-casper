from services.base import BaseService

import boto3


class EC2Service(BaseService):

    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = [
            'aws_instance', 'aws_autoscaling_group', 'aws_security_group'
        ]

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

    def scan_service(self, ghosts):

        def batch(iterable, n=1):
            ln = len(iterable)
            for ndx in range(0, ln, n):
                yield iterable[ndx:min(ndx + n, ln)]

        if len(ghosts['aws_autoscaling_group']['ids']) > 0:
            # get the instances in defaulting asg and add it to the
            # overall defaulting instances

            instances = set(ghosts['aws_instance']['ids'])
            defaulting_asgs = ghosts['aws_autoscaling_group']['ids']
            asg_client = self.session.client('autoscaling')
            for defaulting_asgs_batch in batch(defaulting_asgs, 50):
                asgs = asg_client.describe_auto_scaling_groups(
                    AutoScalingGroupNames=defaulting_asgs_batch
                )
                instances.update([
                    instance['InstanceId'] for sublist in (
                        afull['Instances'] for afull in
                        asgs['AutoScalingGroups']
                    ) for instance in sublist
                ])

                while 'NextToken' in asgs.keys():
                    asgs = asg_client.describe_auto_scaling_groups(
                        AutoScalingGroupNames=defaulting_asgs_batch,
                        NextToken=asgs['NextToken']
                    )
                    instances.update([
                        instance['InstanceId'] for sublist in (
                            afull['Instances'] for afull in
                            asgs['AutoScalingGroups']
                        ) for instance in sublist
                    ])

            ghosts['aws_instance']['ids'] = list(instances)
            ghosts['aws_instance']['count'] = len(
                ghosts['aws_instance']['ids']
            )
