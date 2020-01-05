"""
Casper.

Usage:
    casper.py build [--root-dir=<dir> --bucket-name=<bn> --aws-profile=<profile> --exclude-dirs=<ed> --exclude-state-res=<esr>]
    casper.py scan  [--root-dir=<dir> --bucket-name=<bn> --aws-profile=<profile> --service=<svc> --exclude-cloud-res=<ecr> --rebuild  --summary-only=<b>  --output-file=<f>]
    casper.py -h | --help
    casper.py --version

Options:
    -h --help                               Show this screen.
    --version                               Show version.
    --root-dir=<dir>                        The root terraform directory [default: . ].
    --bucket-name=<bn>                      Bucket name created to save and retrieve state.
    --exclude-dirs=<ed>                     Comma separated list of directories to ignore.
    --exclude-state-res=<res>               Comma separated list of terraform state resources to ignore.
    --aws-profile=<profile>                 AWS profile to use.
    --service=<svc>                         Comma separated list of services to scan, default is to scan all supported services.
    --exclude-cloud-res=<ecr>               Comma separated list of resources ids to ignore.
    --rebuild                               Rebuild and save state first before scanning.
    --summary-only=<b>                      Print only the counts results. [default: True].
    --output-file=<f>                       Output full result to specified file.

"""  # noqa

from docopt import docopt
from states.aws import AWSState
from services.base import (
    get_service, SUPPORTED_SERVICES
)

import logging.config
import logging
import os
import json
import hashlib

# create logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('casper')


class Casper(object):
    def __init__(
        self,
        start_directory: str = None,
        bucket_name: str = "",
        profile: str = None,
        exclude_resources: set = None,
        load_state: bool = False
    ):

        if start_directory is None or start_directory == ".":
            start_directory = os.getcwd()

        if exclude_resources is None:
            exclude_resources = set()

        self.exclude_resources = exclude_resources
        self.start_dir = start_directory
        self.profile = profile

        self.bucket = bucket_name

        self.tf = AWSState(
            profile=self.profile,
            bucket=self.bucket,
            load_state=load_state
        )

    def build(self, exclude_directories=None, exclude_state_res=None):
        return self.tf.build_state_resources(
            start_dir=self.start_dir,
            exclude_directories=exclude_directories,
            exclude_state_res=exclude_state_res
        )

    def scan(self, service_name):

        service = get_service(service_name)
        cloud_service = service(profile=self.profile)

        terraformed_resources = self.tf.state_resources

        ghosts = {}
        for resource_group in cloud_service.resources_groups:
            resources = cloud_service.get_cloud_resources(resource_group)
            diff = set(resources).difference(
                set(terraformed_resources.get(resource_group, []))
            )
            ghosts[resource_group] = {}
            ghosts[resource_group]['ids'] = [
                d for d in diff if d not in self.exclude_resources
            ]
            ghosts[resource_group]['count'] = len(
                ghosts[resource_group]['ids']
            )

        cloud_service.scan_service(ghosts)

        return ghosts


def main(args):
    build_command = args['build']
    scan_command = args['scan']

    aws_profile = args['--aws-profile']

    bucket_name = args['--bucket-name']
    if bucket_name is None:
        casper_bucket = os.environ.get('CASPER_BUCKET', None)
        if casper_bucket:
            bucket_name = casper_bucket
        else:
            print(
                "Please pass the bucket_name argument or use the "
                "CASPER_BUCKET environment variable"
            )
            return

    root_dir = args['--root-dir']

    exclude_dirs = args['--exclude-dirs']
    if exclude_dirs:
        exclude_dirs = set(exclude_dirs.split(","))

    exclude_state_res = args['--exclude-state-res']
    if exclude_state_res:
        exclude_state_res = set(exclude_state_res.split(","))

    service = args['--service']
    if service:
        svc_list = service.split(",")
        service = [s for s in svc_list if s in SUPPORTED_SERVICES]

        if len(service) < len(svc_list):
            logger.warning("Ignoring one or more unsupported services")

        service = set(service)
    else:
        service = SUPPORTED_SERVICES

    exclude_cloud_res = args['--exclude-cloud-res']
    if exclude_cloud_res:
        exclude_cloud_res = set(exclude_cloud_res.split(","))

    rebuild = args['--rebuild']
    summary_only = args['--summary-only']
    output_file = args['--output-file']

    if rebuild:
        build_command = True

    casper = Casper(
        start_directory=root_dir,
        bucket_name=bucket_name,
        profile=aws_profile,
        exclude_resources=exclude_cloud_res,
        load_state=not(build_command)
    )

    if build_command:
        print("Building states...")
        counters = casper.build(
            exclude_state_res=exclude_state_res,
            exclude_directories=exclude_dirs
        )

        # print state statistics
        states = counters['state']
        resource_groups = counters['resource_group']
        resources = counters['resource']

        print("")
        print("Terraform")
        print("--------------------------------------------------------")
        print(f"{states} state(s) checked")
        print(f"{resource_groups} supported resource group(s) discovered")
        print(f"{resources} state resource(s) saved to bucket")

    if scan_command:
        svc_ghost = {}
        print("")
        for svc in service:
            print(svc.upper())
            svc_ghost[svc] = casper.scan(service_name=svc)
            print("--------------------------------------------------------")
            for key in svc_ghost[svc].keys():
                print(f"{svc_ghost[svc][key]['count']} ghost {key} found")
            print("")

        if not summary_only:
            print("--------------------------------------------------------")
            print(json.dumps(svc_ghost, indent=4, sort_keys=True))

        if output_file:
            with open(output_file, 'w') as fid:
                fid.write(json.dumps(svc_ghost, indent=4, sort_keys=True))


# the main block will handle parsing the arguments, options
# and calling the services
if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
