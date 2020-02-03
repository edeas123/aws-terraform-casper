import re
import boto3
import json
import tempfile
import logging
import sys
import os

from casper.terraform import TerraformCommand


IGNORE_PATHS = (".git", ".terraform")
IGNORE_RESOURCE_GROUP = ("terraform_remote_state",)


class CasperState:
    def __init__(self, profile=None, bucket=None, state_file=None):

        self.logger = logging.getLogger("casper")
        self.profile = profile
        self.session = boto3.Session()
        if profile:
            self.session = boto3.Session(profile_name=profile)

        self.bucket = bucket

        self.state_object = "terraform_state"
        if state_file:
            self.state_object = state_file

        self.command = TerraformCommand(profile=self.profile)
        self.state_resources = None

        self._exclude_state_res = set()
        self._counter = {
            "state": 0,
            "resource": 0,
            "resource_group": 0,
        }
        self._resource_group_remap = {
            "aws_spot_instance_request": "aws_instance",
            "aws_lb": "aws_alb",
        }

    def build_state_resources(
        self, start_dir=".", exclude_directories=None, exclude_state_res=None
    ):

        if not exclude_directories:
            exclude_directories = set()

        if not exclude_state_res:
            exclude_state_res = set()

        if self.state_resources is None:
            self.state_resources = {}

        exclude_directories.update(IGNORE_PATHS)
        exclude_state_res.update(IGNORE_RESOURCE_GROUP)
        self._exclude_state_res = exclude_state_res

        for dirpath, dirnames, filenames in os.walk(start_dir):
            dirnames[:] = [d for d in dirnames if d not in exclude_directories]

            if self._is_terraform_state(filenames):
                self.logger.debug(f"In {dirpath}")
                self._list_state_resources(dirpath)

        # save state
        self.save_state()

        return self._counter

    def _list_state_resources(self, state_directory=None):

        # calls terraform state list, formats and returns a list of the result
        r = self.command.run_command("terraform state list", directory=state_directory)
        if r["success"]:
            self._counter["state"] += 1
            resources = [
                resource for resource in r["data"].split("\n") if resource.strip()
            ]

            for resource in resources:
                resource_group = resource.split(".")[-2]
                if resource_group not in self._exclude_state_res:
                    resource_id = self._get_state_resource(state_directory, resource)
                    if resource_id:
                        self._counter["resource"] += 1
                        resource_group_tag = self._resource_group_remap.get(
                            resource_group, resource_group
                        )

                        if self.state_resources.get(resource_group_tag, None):
                            self.state_resources[resource_group_tag].append(resource_id)
                        else:
                            self._counter["resource_group"] += 1
                            self.state_resources[resource_group_tag] = [resource_id]

    def _get_state_resource(self, directory, resource_identifier):

        resource_id = None
        resource_group = resource_identifier.split(".")[-2]
        r = self.command.run_command(
            f"terraform state show {resource_identifier}", directory=directory
        )
        if r["success"]:
            if r["data"]:
                resource_id = self._process_response(resource_group, r["data"])
            else:
                message = (
                    f"'{resource_identifier}' no longer "
                    f"exist in the state: {directory}"
                )
                self.logger.warning(message)

        return resource_id

    def _process_response(self, group, text):
        handler = getattr(self, f"_get_state_{group}", None)
        if handler:
            return handler(text)
        else:
            message = f"State Handler for {group} is not currently supported"
            self.logger.debug(message)
            self._exclude_state_res.add(group)

        return None

    @staticmethod
    def _is_terraform_state(filenames):
        is_state = False
        for filename in filenames:
            if filename.endswith(".tf"):
                is_state = True
                break
        return is_state

    def save_state(self):
        if self.bucket:
            # save to s3 bucket
            self.logger.info("Saving state to s3 bucket ...")
            s3_client = self.session.client("s3")
            try:
                with tempfile.NamedTemporaryFile(mode="w+") as fid:
                    fid.write(json.dumps(self.state_resources))
                    fid.flush()
                    s3_client.upload_file(fid.name, self.bucket, self.state_object)
            except Exception as exc:
                self.logger.error(exc)
                self.logger.warning("Attempting to save state locally instead")
                self.save_state_locally()
        else:
            self.save_state_locally()

    def save_state_locally(self):
        # save to current directory
        self.logger.info("Saving state to current directory ...")
        try:
            with open(self.state_object, "w+") as fid:
                fid.write(json.dumps(self.state_resources))
                fid.flush()
        except Exception as exc:
            self.logger.error(f"Unable to save casper state file. {exc}")
            sys.exit(1)

    def load_state(self):
        if self.bucket:
            # load from s3 bucket
            self.logger.info("Loading state from s3 bucket ...")
            s3 = self.session.resource("s3")
            try:
                obj = s3.Object(self.bucket, self.state_object)
                data = obj.get()["Body"].read()

                self.state_resources = json.loads(data)
            except Exception as exc:
                self.logger.error(exc)
                self.logger.warning("Attempting to load state locally instead")
                self.load_state_locally()
        else:
            self.load_state_locally()

    def load_state_locally(self):
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

    @staticmethod
    def _get_field(field, resource):
        pattern = f"(\\n|^)({field}\\s+.*?)(\\n)"
        match = re.search(pattern, resource)[0]
        value = match.split("=")[1].strip()
        return value

    def _get_state_aws_instance(self, text):
        return self._get_field("id", text)

    def _get_state_aws_autoscaling_group(self, text):
        return self._get_field("id", text)

    def _get_state_aws_spot_instance_request(self, text):
        return self._get_field("spot_instance_id", text)

    def _get_state_aws_security_group(self, text):
        return self._get_field("id", text)

    def _get_state_aws_s3_bucket(self, text):
        return self._get_field("id", text)

    def _get_state_aws_iam_user(self, text):
        return self._get_field("id", text)

    def _get_state_aws_iam_role(self, text):
        return self._get_field("id", text)

    def _get_state_aws_elb(self, text):
        return self._get_field("name", text)

    def _get_state_aws_alb(self, text):
        return self._get_field("name", text)

    def _get_state_aws_lb(self, text):
        return self._get_field("name", text)
