from unittest import TestCase
from unittest.mock import patch
from casper import main, Casper
from casper.state import CasperState
from docopt import docopt
from casper.services.base import SUPPORTED_SERVICES

import os

doc = main.__doc__


@patch("casper.main.run")
@patch("casper.main.docopt")
class TestMainCli(TestCase):
    def test_build_no_other_args(self, mock_docopt, mock_run):

        test_args = ["build"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None,
            bucket_name=None,
            build_command=True,
            detailed=False,
            exclude_cloud_res=None,
            exclude_dirs=None,
            exclude_state_res=None,
            loglevel="INFO",
            output_file=None,
            root_dir=".",
            scan_command=False,
            services_list=None,
            state_file="terraform_state",
        )

    @patch("casper.main.os")
    def test_build_with_bucket_name_env(self, mock_os, mock_docopt, mock_run):
        def mock_get(key, default):
            if key == "CASPER_BUCKET":
                return "test_bucket"
            return default

        test_args = ["build"]
        mock_os.environ.get.side_effect = mock_get
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None,
            bucket_name="test_bucket",
            build_command=True,
            detailed=False,
            exclude_cloud_res=None,
            exclude_dirs=None,
            exclude_state_res=None,
            loglevel="INFO",
            output_file=None,
            root_dir=".",
            scan_command=False,
            services_list=None,
            state_file="terraform_state",
        )

    def test_scan_no_other_args(self, mock_docopt, mock_run):

        test_args = ["scan"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None,
            bucket_name=None,
            build_command=False,
            detailed=False,
            exclude_cloud_res=None,
            exclude_dirs=None,
            exclude_state_res=None,
            loglevel="INFO",
            output_file=None,
            root_dir=".",
            scan_command=True,
            services_list=None,
            state_file="terraform_state",
        )

    def test_scan_with_rebuild(self, mock_docopt, mock_run):

        test_args = ["scan", "--rebuild", "--exclude-dirs=.fakedir1,.fakedir2"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None,
            bucket_name=None,
            build_command=True,
            detailed=False,
            exclude_cloud_res=None,
            exclude_dirs=[".fakedir1", ".fakedir2"],
            exclude_state_res=None,
            loglevel="INFO",
            output_file=None,
            root_dir=".",
            scan_command=True,
            services_list=None,
            state_file="terraform_state",
        )

    def test_scan_with_exclude_cloud_res(self, mock_docopt, mock_run):

        test_args = ["scan", "--exclude-cloud-res=aws_abc,aws_def"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None,
            bucket_name=None,
            build_command=False,
            detailed=False,
            exclude_cloud_res=["aws_abc", "aws_def"],
            exclude_dirs=None,
            exclude_state_res=None,
            loglevel="INFO",
            output_file=None,
            root_dir=".",
            scan_command=True,
            services_list=None,
            state_file="terraform_state",
        )


@patch("casper.main.docopt")
class TestMainRun(TestCase):
    @patch.object(Casper, "scan")
    @patch.object(Casper, "build")
    def test_run_build(self, mock_build, mock_scan, mock_docopt):
        test_args = [
            "build",
            "--exclude-state-res=fake.state,unknown.state",
            "--exclude-dirs=fakedir1,fakedir2",
        ]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_build.assert_called_with(
            exclude_directories={"fakedir1", "fakedir2"},
            exclude_state_res={"fake.state", "unknown.state"},
        )
        mock_scan.assert_not_called()

    @patch.object(CasperState, "load_state")
    @patch.object(Casper, "scan")
    @patch.object(Casper, "build")
    def test_run_scan(self, mock_build, mock_scan, _, mock_docopt):

        test_args = ["scan", "--services=ec2,iam"]
        mock_docopt.return_value = docopt(doc, test_args)
        mock_scan.side_effect = [
            {"aws_instance": {"count": 1, "ids": ["test_instance"]}},
            {"iam_role": {"count": 2, "ids": ["test_role", "fake_role"]}},
        ]
        main.cli()

        mock_build.assert_not_called()
        self.assertEqual(2, mock_scan.call_count)

    @patch.object(CasperState, "load_state")
    @patch.object(Casper, "scan")
    @patch.object(Casper, "build")
    def test_run_scan_all_supported_services(
        self, mock_build, mock_scan, _, mock_docopt
    ):
        test_args = ["scan"]
        mock_docopt.return_value = docopt(doc, test_args)
        main.cli()
        mock_build.assert_not_called()

        self.assertEqual(len(SUPPORTED_SERVICES), mock_scan.call_count)

    @patch.object(CasperState, "load_state")
    @patch.object(Casper, "scan")
    @patch.object(Casper, "build")
    def test_run_scan_with_fake_service(self, mock_build, mock_scan, _, mock_docopt):
        test_args = ["scan", "--services=ec2,fake"]
        mock_docopt.return_value = docopt(doc, test_args)
        main.cli()
        mock_build.assert_not_called()

        self.assertEqual(1, mock_scan.call_count)

    @patch.object(CasperState, "load_state")
    @patch.object(Casper, "scan")
    @patch.object(Casper, "build")
    def test_run_scan_with_all_fake_service(
        self, mock_build, mock_scan, _, mock_docopt
    ):
        test_args = ["scan", "--services=fake1,fake2"]
        mock_docopt.return_value = docopt(doc, test_args)
        main.cli()
        mock_build.assert_not_called()

        self.assertEqual(0, mock_scan.call_count)

    @patch.object(CasperState, "load_state")
    @patch.object(Casper, "scan")
    def test_run_scan_with_output_file(self, mock_scan, _, mock_docopt):
        testfile = "testjson.txt"
        test_args = ["scan", "--services=ec2,iam", f"--output-file={testfile}"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()

        self.assertEqual(2, mock_scan.call_count)
        self.assertTrue(os.path.exists(testfile))

        if os.path.exists(testfile):
            os.remove(testfile)
