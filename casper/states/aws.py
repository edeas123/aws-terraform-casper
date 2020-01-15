from casper.states.terraform import TerraformState

import re
import boto3
import json
import tempfile


class AWSState(TerraformState):

    def __init__(
        self,
        profile=None,
        bucket=None,
        state_file=None,
        load_state=False
    ):
        self._resource_group_remap = {
            'aws_spot_instance_request': 'aws_instance',
            'aws_lb': 'aws_alb'
        }
        self.session = boto3.Session()
        self.state_object = state_file

        if profile:
            self.session = boto3.Session(profile_name=profile)

        super().__init__(profile=profile, bucket=bucket, load_state=load_state)

    def _save_state(self):
        s3_client = self.session.client('s3')
        with tempfile.NamedTemporaryFile(mode='w+') as fid:
            fid.write(json.dumps(self.state_resources))
            fid.flush()
            s3_client.upload_file(
                fid.name, self.bucket, self.state_object
            )

    def _load_state(self):
        s3 = self.session.resource('s3')
        obj = s3.Object(self.bucket, self.state_object)
        data = obj.get()['Body'].read()

        self.state_resources = json.loads(data)

    @classmethod
    def _get_field(cls, field, resource):
        pattern = f"(\\n|^)({field}\\s+.*?)(\\n)"
        match = re.search(pattern, resource)[0]
        value = match.split("=")[1].strip()
        return value

    def _get_state_aws_instance(self, text):
        return self._get_field('id', text)

    def _get_state_aws_autoscaling_group(self, text):
        return self._get_field('id', text)

    def _get_state_aws_spot_instance_request(self, text):
        return self._get_field('spot_instance_id', text)

    def _get_state_aws_security_group(self, text):
        return self._get_field('id', text)

    def _get_state_aws_s3_bucket(self, text):
        return self._get_field('id', text)

    def _get_state_aws_iam_user(self, text):
        return self._get_field('id', text)

    def _get_state_aws_iam_role(self, text):
        return self._get_field('id', text)

    def _get_state_aws_elb(self, text):
        return self._get_field('name', text)

    def _get_state_aws_alb(self, text):
        return self._get_field('name', text)

    def _get_state_aws_lb(self, text):
        return self._get_field('name', text)
