from casper.services.base import BaseService


class IAMService(BaseService):
    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = ["aws_iam_user", "aws_iam_role"]

    def scan_service(self, ghosts):
        pass
