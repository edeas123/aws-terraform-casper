from unittest import TestCase
from unittest.mock import Mock, patch
from casper.main import Casper


@patch('casper.command.TerraformCommand.run_command')
class TestMainInterface(TestCase):

    def setUp(self) -> None:
        pass

    def test_run(self, fake_run):

        pass

    def test_build(self, fake_run):
        pass

    @patch('casper.main.get_service')
    def test_scan(self, fake_get_service, fake_run):
        casper = Casper()
        # fake_get_service.return_value = Mock(
        #     resources_groups=[]
        # )
        casper.scan('ec2')
        print()
        print(fake_get_service.call_count)
        print(fake_run.call_count)
        pass
