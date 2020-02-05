from casper.services import Service, Resource


class AwsS3BucketResource(Resource):

    _tag = "aws_s3_bucket"

    def get_cloud_resource(self):
        s3_client = self.session.client("s3")
        s3_buckets = s3_client.list_buckets()
        buckets = {bucket["Name"]: bucket for bucket in s3_buckets["Buckets"]}

        return buckets


class S3Service(Service):
    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = ["aws_s3_bucket"]
