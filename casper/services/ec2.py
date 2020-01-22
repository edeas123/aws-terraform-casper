from casper.services.base import BaseService


class EC2Service(BaseService):

    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = [
            'aws_instance', 'aws_autoscaling_group', 'aws_security_group',
            'aws_alb', 'aws_elb'
        ]

    def _get_live_aws_alb(self):
        alb_client = self.session.client('elbv2')
        alb = alb_client.describe_load_balancers()
        lbs = {
            lb['LoadBalancerName']: lb
            for lb in alb['LoadBalancers']
        }

        return lbs

    def _get_live_aws_elb(self):
        elb_client = self.session.client('elb')
        elb = elb_client.describe_load_balancers()
        lbs = {
            lb['LoadBalancerName']: lb
            for lb in elb['LoadBalancerDescriptions']
        }

        return lbs

    def _get_live_aws_instance(self):

        ec2_client = self.session.client('ec2')
        ec2 = ec2_client.describe_instances()
        instances = [
            reservation['Instances']
            for reservation in ec2['Reservations']
        ]
        ec2s = {
            instance['InstanceId']: instance for instance_group in instances
            for instance in instance_group if instance['State']['Code'] == 16
        }

        # TODO: find better way of doing thing
        # remove dynamic instances
        asg_client = self.session.client('autoscaling')
        asgs = asg_client.describe_auto_scaling_instances()

        dynamic_instances = [
            instance['InstanceId'] for instance in asgs['AutoScalingInstances']
        ]
        while 'NextToken' in asgs.keys():
            asgs = asg_client.describe_auto_scaling_instances(
                NextToken=asgs['NextToken']
            )
            dynamic_instances.extend(
                instance['InstanceId']
                for instance in asgs['AutoScalingInstances']
            )

        static_instances = {
            k: ec2s[k] for k in
            set(ec2s.keys()).difference(set(dynamic_instances))
        }

        return static_instances

    def _get_live_aws_autoscaling_group(self):

        asg_client = self.session.client('autoscaling')
        asgs_group = asg_client.describe_auto_scaling_groups()
        asgs = {
            a['AutoScalingGroupName']: a
            for a in asgs_group['AutoScalingGroups']
        }

        while 'NextToken' in asgs_group.keys():
            asgs_group = asg_client.describe_auto_scaling_groups(
                NextToken=asgs_group['NextToken']
            )
            asgs.update({
                a['AutoScalingGroupName']: a
                for a in asgs_group['AutoScalingGroups']
            })

        return asgs

    def _get_live_aws_security_group(self):
        ec2_client = self.session.client('ec2')

        sgs_group = ec2_client.describe_security_groups()
        sgs = {sg['GroupId']: sg for sg in sgs_group['SecurityGroups']}

        while 'NextToken' in sgs_group.keys():
            sgs_group = ec2_client.describe_security_groups(
                NextToken=sgs_group['NextToken']
            )
            sgs.update(
                {sg['GroupId']: sg for sg in sgs_group['SecurityGroups']}
            )

        return sgs

    def scan_service(self, ghosts):

        def batch(iterable, n=1):
            ln = len(iterable)
            for ndx in range(0, ln, n):
                yield iterable[ndx:min(ndx + n, ln)]

        if (
            'aws_autoscaling_group' in ghosts and
            len(ghosts['aws_autoscaling_group']['ids']) > 0
        ):
            # get the instances in defaulting asg and add it to the
            # overall defaulting instances

            instances = set(ghosts['aws_instance']['ids'])
            defaulting_asgs = ghosts['aws_autoscaling_group']['ids']
            asg_instances = {}

            asg_client = self.session.client('autoscaling')
            for defaulting_asgs_batch in batch(defaulting_asgs, 50):
                asgs = asg_client.describe_auto_scaling_groups(
                    AutoScalingGroupNames=defaulting_asgs_batch
                )
                asg_instances.update({
                    instance['InstanceId']: instance for sublist in (
                        afull['Instances'] for afull in
                        asgs['AutoScalingGroups']
                    ) for instance in sublist
                })

                while 'NextToken' in asgs.keys():
                    asgs = asg_client.describe_auto_scaling_groups(
                        AutoScalingGroupNames=defaulting_asgs_batch,
                        NextToken=asgs['NextToken']
                    )
                    asg_instances.update({
                        instance['InstanceId']: instance for sublist in (
                            afull['Instances'] for afull in
                            asgs['AutoScalingGroups']
                        ) for instance in sublist
                    })

            instances.update(asg_instances.keys())

            ghosts['aws_instance']['ids'] = list(instances)
            ghosts['aws_instance']['count'] = len(
                ghosts['aws_instance']['ids']
            )

            if 'resources' in ghosts['aws_instance']:
                asg_instances.update({
                    r['InstanceId']: r
                    for r in ghosts['aws_instance']['resources']
                })

                resources = [
                    asg_instances.get(k)
                    for k in ghosts['aws_instance']['ids']
                ]

                ghosts['aws_instance']['resources'] = resources
