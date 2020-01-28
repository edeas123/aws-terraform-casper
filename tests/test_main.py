from unittest import TestCase
from unittest.mock import patch
from casper import main
from docopt import docopt

doc = main.__doc__


@patch('casper.main.run')
@patch('casper.main.docopt')
class TestMainCli(TestCase):
    def test_build_no_other_args(self, mock_docopt, mock_run):

        test_args = ["build"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None, bucket_name=None, build_command=True,
            detailed=False, exclude_cloud_res=None,
            exclude_dirs=None, exclude_state_res=None, loglevel='INFO',
            output_file=None, root_dir='.',
            scan_command=False, services_list=[],
            state_file='terraform_state'
        )

    @patch('casper.main.os')
    def test_build_with_bucket_name_env(self, mock_os, mock_docopt, mock_run):

        def mock_get(key, default):
            if key == 'CASPER_BUCKET':
                return 'test_bucket'
            return default

        test_args = ["build"]
        mock_os.environ.get.side_effect = mock_get
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None, bucket_name='test_bucket', build_command=True,
            detailed=False, exclude_cloud_res=None,
            exclude_dirs=None, exclude_state_res=None, loglevel='INFO',
            output_file=None, root_dir='.',
            scan_command=False, services_list=[],
            state_file='terraform_state'
        )

    def test_scan_no_other_args(self, mock_docopt, mock_run):

        test_args = ["scan"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None, bucket_name=None, build_command=False,
            detailed=False, exclude_cloud_res=None,
            exclude_dirs=None, exclude_state_res=None, loglevel='INFO',
            output_file=None, root_dir='.',
            scan_command=True, services_list=[],
            state_file='terraform_state'
        )

    def test_scan_with_rebuild(self, mock_docopt, mock_run):

        test_args = ["scan", "--rebuild"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None, bucket_name=None, build_command=True,
            detailed=False, exclude_cloud_res=None,
            exclude_dirs=None, exclude_state_res=None, loglevel='INFO',
            output_file=None, root_dir='.',
            scan_command=True, services_list=[],
            state_file='terraform_state'
        )

    def test_scan_with_services(self, mock_docopt, mock_run):

        test_args = ["scan", "--services=abc,def"]
        mock_docopt.return_value = docopt(doc, test_args)

        main.cli()
        mock_run.assert_called_with(
            aws_profile=None, bucket_name=None, build_command=False,
            detailed=False, exclude_cloud_res=None,
            exclude_dirs=None, exclude_state_res=None, loglevel='INFO',
            output_file=None, root_dir='.',
            scan_command=True, services_list=['abc', 'def'],
            state_file='terraform_state'
        )
 