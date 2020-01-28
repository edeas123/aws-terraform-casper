from casper.services.base import BaseService


class IAMService(BaseService):

    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = [
            'aws_iam_user',
            'aws_iam_role'
        ]

    def _get_live_aws_iam_user(self):

        iam_client = self.session.client('iam')
        iam_users = iam_client.list_users()
        users = {
            user['UserName']: user
            for user in iam_users['Users']
        }

        return users

    def _get_live_aws_iam_role(self):

        iam_client = self.session.client('iam')
        iam_roles = iam_client.list_roles()
        roles = {
            role['RoleName']: role
            for role in iam_roles['Roles']
        }

        return roles

    def scan_service(self, ghosts):
        pass
