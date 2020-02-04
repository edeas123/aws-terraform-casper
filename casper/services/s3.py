from casper.services.base import BaseService


class S3Service(BaseService):
    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = ["aws_s3_bucket"]

    def scan_service(self, ghosts):
        pass
