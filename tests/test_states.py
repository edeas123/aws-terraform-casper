from unittest import TestCase
from casper.state import CasperState

from unittest.mock import patch
import os
import shutil
import pytest
import boto3
import json

from moto import mock_s3
from tests.utils import aws_credentials, load_sample


class TestState(TestCase):
    root_dir = "temp"

    @classmethod
    def _make_dir(cls, path):
        os.makedirs(path, exist_ok=True)

    @classmethod
    def _make_file(cls, path):
        with open(path, "w") as f:
            f.write("test")

    def setUp(self) -> None:
        self.state = CasperState()
        self._make_dir(self.root_dir)

    @patch("casper.terraform.TerraformCommand.run_command")
    @patch.object(CasperState, "save_state")
    def test_build_state_resources_state_management(self, mock_save, cmd):
        self._make_dir(os.path.join(self.root_dir, "main"))
        self._make_file(os.path.join(self.root_dir, "main", "real.tf"))

        self._make_dir(os.path.join(self.root_dir, "fake"))
        self._make_file(os.path.join(self.root_dir, "fake", "fake.txt"))

        self._make_dir(os.path.join(self.root_dir, "vars"))
        self._make_file(os.path.join(self.root_dir, "vars", "real1.tfvars"))

        self._make_dir(os.path.join(self.root_dir, ".git"))
        self._make_file(os.path.join(self.root_dir, ".git", "git.tf"))

        self.state.build_state_resources(start_dir=self.root_dir)
        self.assertEqual(
            1,
            cmd.call_count,
            "Should be called once times to list the resources in the only "
            "unexcluded directory with a .tf file",
        )
        mock_save.assert_called_once()

    @patch("casper.terraform.TerraformCommand.run_command")
    @patch.object(CasperState, "save_state")
    def test_build_state_resource_state_management_exclude_specific_dir(self, _, cmd):
        self._make_dir(os.path.join(self.root_dir, "main"))
        self._make_file(os.path.join(self.root_dir, "main", "real.tf"))

        self._make_dir(os.path.join(self.root_dir, "exclude1"))
        self._make_file(os.path.join(self.root_dir, "exclude1", "exclude1.tf"))

        self._make_dir(os.path.join(self.root_dir, "exclude2"))
        self._make_file(os.path.join(self.root_dir, "exclude2", "exclude2.tf"))

        self.state.build_state_resources(
            start_dir=self.root_dir, exclude_directories={"exclude1", "exclude2"}
        )
        self.assertEqual(
            1,
            cmd.call_count,
            "Should be called once times to list the resources in the only "
            "unexcluded directory with a .tf file",
        )

    @patch("casper.terraform.TerraformCommand.run_command")
    @patch.object(CasperState, "save_state")
    def test_build_state_resources_exclude_specific_state_resource(self, _, cmd):
        self._make_dir(os.path.join(self.root_dir, "main"))
        self._make_file(os.path.join(self.root_dir, "main", "real.tf"))

        cmd.side_effect = [
            {"success": True, "data": load_sample("state_specific_exclude.txt")},
            {"success": True, "data": load_sample("aws_lb.txt")},
        ]

        self.state.build_state_resources(
            start_dir=self.root_dir, exclude_state_res={"exclude_me"}
        )
        self.assertEqual(
            2,
            cmd.call_count,
            "Should be called two times, 1 to list the resource in the "
            "state, the other to show the only unexcluded resource in the state",
        )
        self.assertEqual(
            {"aws_alb": ["test-lb"],}, self.state.state_resources,
        )

    @patch("casper.terraform.TerraformCommand.run_command")
    @patch.object(CasperState, "save_state")
    def test_build_state_resources(self, _, cmd):
        self._make_dir(os.path.join(self.root_dir, "main"))
        self._make_file(os.path.join(self.root_dir, "main", "real.tf"))

        cmd.side_effect = [
            {"success": True, "data": load_sample("state.txt")},
            {"success": True, "data": load_sample("aws_spot_instance_request.txt")},
            {"success": True, "data": load_sample("aws_instance.txt")},
            {"success": True, "data": load_sample("aws_lb.txt")},
        ]

        self.state.build_state_resources(start_dir=self.root_dir)
        self.assertEqual(
            4,
            cmd.call_count,
            "Should be called three times, 1 to list the resource in the "
            "state, the other to show the three resource in the state",
        )
        self.assertEqual(
            {
                "aws_alb": ["test-lb"],
                "aws_instance": ["i-0101522650aeaa2dd", "i-084699b83473e2c69"],
            },
            self.state.state_resources,
        )

    @patch("casper.terraform.TerraformCommand.run_command")
    @patch.object(CasperState, "save_state")
    @patch("logging.Logger.warning")
    def test_build_state_resources_removed_resource(self, logger, _, cmd):
        self._make_dir(os.path.join(self.root_dir, "main"))
        self._make_file(os.path.join(self.root_dir, "main", "real.tf"))

        cmd.side_effect = [
            {"success": True, "data": load_sample("state_removed_resource.txt")},
            {"success": True, "data": load_sample("empty.txt")},
        ]

        self.state.build_state_resources(start_dir=self.root_dir)
        self.assertEqual(
            2,
            cmd.call_count,
            "Should be called two times, 1 to list the resource in the "
            "state, the other to show the only resource in the state",
        )
        logger.assert_called_with(
            "'aws_instance.empty' no longer exist in the state: temp/main"
        )

    @patch("casper.terraform.TerraformCommand.run_command")
    @patch.object(CasperState, "save_state")
    @patch("logging.Logger.debug")
    def test_build_state_resources_unsupported_resource(self, logger, _, cmd):
        self._make_dir(os.path.join(self.root_dir, "main"))
        self._make_file(os.path.join(self.root_dir, "main", "real.tf"))

        cmd.side_effect = [
            {"success": True, "data": load_sample("state_unsupported_resource.txt")},
            {"success": True, "data": load_sample("fake_unsupported_resource.txt")},
        ]

        self.state.build_state_resources(start_dir=self.root_dir)
        self.assertEqual(
            2,
            cmd.call_count,
            "Should be called two times, 1 to list the resource in the "
            "state, the other to show the only resource in the state",
        )
        logger.assert_called_with(
            "State Handler for fake_unsupported_resource is not currently supported"
        )

    @mock_s3
    @pytest.mark.usefixtures("aws_credentials")
    def test_save_state_s3(self):
        bucket = "Test"
        conn = boto3.resource("s3")
        conn.create_bucket(Bucket=bucket)

        state = CasperState(bucket=bucket)
        test_data = {"test": "me"}
        state.state_resources = test_data
        state.save_state()

        obj = conn.Object(state.bucket, state.state_object)
        data = json.loads(obj.get()["Body"].read())

        self.assertEqual(test_data, data)

    @mock_s3
    @pytest.mark.usefixtures("aws_credentials")
    def test_save_state_local_failback(self):
        bucket = "Test"
        state = CasperState(bucket=bucket)
        test_data = {"test": "me"}
        state.state_resources = test_data
        state.save_state()

        with open(state.state_object, "r") as fid:
            data = fid.read()
            data = json.loads(data)

        self.assertEqual(test_data, data)
        if os.path.exists(state.state_object):
            os.remove(state.state_object)

    @mock_s3
    @pytest.mark.usefixtures("aws_credentials")
    def test_load_state_s3(self):
        bucket = "Test"
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=bucket)

        state = CasperState(bucket=bucket)
        test_data = {"test": "me2"}
        conn.put_object(
            Bucket=state.bucket, Key=state.state_object, Body=json.dumps(test_data)
        )

        state.load_state()
        self.assertEqual(test_data, state.state_resources)

    @mock_s3
    @pytest.mark.usefixtures("aws_credentials")
    def test_load_state_local_failback(self):
        bucket = "Test"
        state = CasperState(bucket=bucket)
        test_data = {"test": "me2"}

        with open(state.state_object, "w+") as fid:
            fid.write(json.dumps(test_data))

        state.load_state()
        self.assertEqual(test_data, state.state_resources)

        if os.path.exists(state.state_object):
            os.remove(state.state_object)

    def tearDown(self):
        shutil.rmtree(self.root_dir, ignore_errors=True)
