from casper.states.terraform import TerraformState

import re
import boto3
import json
import tempfile
import logging
import sys


class AWSState(TerraformState):

    def __init__(
        self,
        profile=None,
        bucket=None,
        state_file=None,
        load_state=False
    ):
        self.logger = logging.getLogger('casper')
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
        if self.bucket:
            # save to s3 bucket
            self.logger.info("Saving state to s3 bucket ...")
            s3_client = self.session.client('s3')
            try:
                with tempfile.NamedTemporaryFile(mode='w+') as fid:
                    fid.write(json.dumps(self.state_resources))
                    fid.flush()
                    s3_client.upload_file(
                        fid.name, self.bucket, self.state_object
                    )
            except Exception as exc:
                self.logger.error(exc)
                self.logger.warning(
                    "Attempting to save state locally instead"
                )
                self._save_state_locally()
        else:
            self._save_state_locally()

    def _save_state_locally(self):
        # save to current directory
        self.logger.info("Saving state to current directory ...")
        try:
            with open(self.state_object, 'w+') as fid:
                fid.write(json.dumps(self.state_resources))
                fid.flush()
        except Exception as exc:
            self.logger.error(
                f"Unable to save casper state file. {exc}"
            )
            sys.exit(1)

    def _load_state(self):
        if self.bucket:
            # load from s3 bucket
            self.logger.info("Loading state from s3 bucket ...")
            s3 = self.session.resource('s3')
            try:
                obj = s3.Object(self.bucket, self.state_object)
                data = obj.get()['Body'].read()

                self.state_resources = json.loads(data)
            except Exception as exc:
                self.logger.error(exc)
                self.logger.warning(
                    "Attempting to load state locally instead"
                )
                self._load_state_locally()
        else:
            self._load_state_locally()

    def _load_state_locally(self):
        # load from current directory
        self.logger.info("Loading state from current directory ...")
        try:
            with open(self.state_object, "r") as fid:
                data = fid.read()
                self.state_resources = json.loads(data)
        except FileNotFoundError:
            self.logger.error(
                f"Unable to find local casper state file: {self.state_object}"
            )
            sys.exit(1)
        except Exception as exc:
            self.logger.error(f"Unknown Exception: {exc}")
            sys.exit(1)

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
