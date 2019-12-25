"""
Casper.

Usage:
    casper.py <service> <start-dir> [options]

Options:
    -h --help                               Show this screen.
    --version                               Show version.
    --refresh-state                         If the state should be rescaned to refresh the state database.
    --aws-profile=<profile>                 AWS profile to use
    --exclude-dirs=<dir>                    Comma seperated list of directories to ignore
    --exclude-res=<res>                     Comma seperated list of aws resources ids to ignore
    --s3bucket=<b>                           S3 bucket to save and refresh state from, required if --refresh-state is not set
    --detailed                              Show details of the ghost resources

"""  # noqa

from docopt import docopt
from terraform_state import TerraformState
from services.base import (
    get_service, SUPPORTED_SERVICES, UnsupportedServiceException
)


class Casper(object):
    def __init__(
        self, start_directory: str = None, profile: str = None,
        refresh_local_state: bool = False, exclude_directories: set = None,
        exclude_resources: set = None, bucket: str = None
    ):

        if exclude_resources is None:
            exclude_resources = set()

        self.profile = profile
        self.excluded_resources = exclude_resources
        self.tf = TerraformState(
            start_directory,
            profile=profile,
            refresh_state=refresh_local_state,
            exclude_directories=exclude_directories,
            bucket=bucket
        )

    def find_ghosts(self, service: str, detailed: bool = False):

        service = get_service(service)

        tf_service = service(vendor="terraform", profile=self.profile)
        cloud_service = service(vendor="aws", profile=self.profile)

        terraformed_resources = self.tf.get_service_resources(
            service=tf_service
        )

        ghosts = {}
        for resource_group in cloud_service.resources_groups.keys():
            resource_group_tag = cloud_service.resources_groups[resource_group]
            resources = (
                cloud_service.get_cloud_resources(
                    resource_group
                )
            )
            diff = set(resources).difference(
                set(terraformed_resources[resource_group_tag])
            )
            ghosts[resource_group_tag] = {}
            ghosts[resource_group_tag]['ids'] = [
                d for d in diff if d not in self.excluded_resources
            ]
            ghosts[resource_group_tag]['count'] = len(
                ghosts[resource_group_tag]['ids']
            )

        cloud_service.scan_service(ghosts)

        if detailed:
            pass

        return ghosts


# the main block will handle parsing the arguments, options
# and calling the services
if __name__ == '__main__':
    args = docopt(__doc__)

    service = args['<service>']

    if service not in SUPPORTED_SERVICES:
        message = f"The {service} service is not currently supported"
        raise UnsupportedServiceException(message)

    start_dir = args['<start-dir>']

    refresh_state = args['--refresh-state']
    aws_profile = args['--aws-profile']
    exclude_dirs = args['--exclude-dirs']
    if exclude_dirs:
        exclude_dirs = set(exclude_dirs.split(","))

    exclude_res = args['--exclude-res']
    if exclude_res:
        exclude_res = set(exclude_res.split(","))

    detailed = args['--detailed']
    s3bucket = args['--s3bucket']

    # scan and build terraform state
    casper = Casper(
        start_directory=start_dir, profile=aws_profile,
        refresh_local_state=refresh_state,
        exclude_directories=exclude_dirs,
        exclude_resources=exclude_res,
        bucket=s3bucket
    )

    # this would return a dictionary of service subcategory
    # (e.g ec2instances, securitygroups etc), and the ids of the resources found
    # for those categories
    # find the difference and print to file or
    ghosts = casper.find_ghosts(service=service, detailed=detailed)
    print(ghosts)
