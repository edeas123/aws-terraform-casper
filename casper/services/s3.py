from casper.services.base import BaseService


class S3Service(BaseService):

    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = [
            'aws_s3_bucket'
        ]

    def _get_live_aws_s3_bucket(self):

        s3_client = self.session.client('s3')
        s3_buckets = s3_client.list_buckets()
        buckets = {
            bucket['Name']: bucket
            for bucket in s3_buckets['Buckets']
        }

        return buckets

    def scan_service(self, ghosts):
        pass
