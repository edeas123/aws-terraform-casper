from services.base import BaseService


class IAMService(BaseService):

    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = [
            'aws_iam_user'
        ]

    def _get_live_aws_iam_user(self):

        iam_client = self.session.client('iam')
        iam_users = iam_client.list_users()
        users = [
            user['UserName']
            for user in iam_users['Users']
        ]

        return users

    def scan_service(self, ghosts):
        pass
