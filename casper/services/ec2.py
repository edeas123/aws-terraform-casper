from casper.services.base import BaseService


class EC2Service(BaseService):
    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = [
            "aws_instance",
            "aws_autoscaling_group",
            "aws_security_group",
            "aws_alb",
            "aws_elb",
        ]

    def scan_service(self, ghosts):
        def batch(iterable, n=1):
            ln = len(iterable)
            for ndx in range(0, ln, n):
                yield iterable[ndx : min(ndx + n, ln)]

        if (
            "aws_autoscaling_group" in ghosts
            and len(ghosts["aws_autoscaling_group"]["ids"]) > 0
        ):
            # get the instances in defaulting asg and add it to the
            # overall defaulting instances

            instances = set(ghosts["aws_instance"]["ids"])
            defaulting_asgs = ghosts["aws_autoscaling_group"]["ids"]
            asg_instances = {}

            asg_client = self.session.client("autoscaling")
            for defaulting_asgs_batch in batch(defaulting_asgs, 50):
                asgs = asg_client.describe_auto_scaling_groups(
                    AutoScalingGroupNames=defaulting_asgs_batch
                )
                asg_instances.update(
                    {
                        instance["InstanceId"]: instance
                        for sublist in (
                            afull["Instances"] for afull in asgs["AutoScalingGroups"]
                        )
                        for instance in sublist
                    }
                )

                while "NextToken" in asgs.keys():
                    asgs = asg_client.describe_auto_scaling_groups(
                        AutoScalingGroupNames=defaulting_asgs_batch,
                        NextToken=asgs["NextToken"],
                    )
                    asg_instances.update(
                        {
                            instance["InstanceId"]: instance
                            for sublist in (
                                afull["Instances"]
                                for afull in asgs["AutoScalingGroups"]
                            )
                            for instance in sublist
                        }
                    )

            instances.update(asg_instances.keys())

            ghosts["aws_instance"]["ids"] = list(instances)
            ghosts["aws_instance"]["count"] = len(ghosts["aws_instance"]["ids"])

            if "resources" in ghosts["aws_instance"]:
                asg_instances.update(
                    {r["InstanceId"]: r for r in ghosts["aws_instance"]["resources"]}
                )

                resources = [
                    asg_instances.get(k) for k in ghosts["aws_instance"]["ids"]
                ]

                ghosts["aws_instance"]["resources"] = resources
