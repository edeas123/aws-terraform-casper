from state.terraform import TerraformState

import re
import boto3


class AWSState(TerraformState):

    def __init__(
        self,
        profile=None,
        bucket=None
    ):
        super().__init__(profile=profile, bucket=bucket)
        self._resource_group_remap = {
            'aws_spot_instance_request': 'aws_instance'
        }

    def _save_state(self):
        pass

    @classmethod
    def _get_field(cls, field, resource):
        pattern = f"(?<={field})(.*?)(?=\\n)"
        return re.search(pattern, resource)[0].lstrip(' =')

    def _get_state_aws_instance(self, text):
        return self._get_field('id', text)

    def _get_state_aws_autoscaling_group(self, text):
        return self._get_field('id', text)

    def _get_state_aws_spot_instance_request(self, text):
        return self._get_field('spot_instance_id', text)

    def _get_state_aws_security_group(self, text):
        return self._get_field('id', text)
