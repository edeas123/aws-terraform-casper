from casper.services import Service, Resource


class AwsIamUserResource(Resource):

    _tag = "aws_iam_user"

    def get_cloud_resource(self):
        iam_client = self.session.client("iam")
        iam_users = iam_client.list_users()
        users = {user["UserName"]: user for user in iam_users["Users"]}

        return users


class AwsIamRoleResource(Resource):

    _tag = "aws_iam_role"

    def get_cloud_resource(self):
        iam_client = self.session.client("iam")
        iam_roles = iam_client.list_roles()
        roles = {role["RoleName"]: role for role in iam_roles["Roles"]}

        return roles


class IAMService(Service):
    def __init__(self, profile: str = None):

        super().__init__(profile=profile)
        self._resources_groups = ["aws_iam_user", "aws_iam_role"]
