"""
Casper.

Usage:
    casper.py build [--root-dir=<dir> --bucket-name=<bn> --state-file=<sf> --aws-profile=<profile> --exclude-dirs=<ed> --exclude-state-res=<esr> --loglevel=<lvl>]
    casper.py scan  [--root-dir=<dir> --bucket-name=<bn> --state-file=<sf> --aws-profile=<profile> --services=<svc> --exclude-cloud-res=<ecr> --rebuild --detailed --output-file=<f>  --loglevel=<lvl>]
    casper.py -h | --help
    casper.py --version

Options:
    -h --help                               Show this screen.
    --version                               Show version.
    --root-dir=<dir>                        The root terraform directory [default: . ].
    --bucket-name=<bn>                      Bucket name created to save and retrieve state.
    --state-file=<sf>                       Name used to save state file in the bucket [default: terraform_state].
    --exclude-dirs=<ed>                     Comma separated list of directories to ignore.
    --exclude-state-res=<res>               Comma separated list of terraform state resources to ignore.
    --aws-profile=<profile>                 AWS profile to use.
    --services=<svc>                        Comma separated list of services to scan, default is to scan all supported services.
    --exclude-cloud-res=<ecr>               Comma separated list of resources ids to ignore.
    --rebuild                               Rebuild and save state first before scanning.
    --detailed                              Retrieve and include details about the resources discovered through scan.
    --output-file=<f>                       Output full result to specified file.
    --loglevel=<lvl>                        Log level [default: INFO].

"""  # noqa

from docopt import docopt
import os
import json
import logging
import logging.config

from casper.services.base import SUPPORTED_SERVICES
from casper import Casper


def _setup_logging(loglevel='INFO'):

    # create logger
    logger = logging.getLogger('casper')
    numeric_level = getattr(logging, loglevel.upper(), None)

    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    logger.setLevel(numeric_level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


def cli():

    # get the commandline arguments
    args = docopt(__doc__)

    # setup logging
    loglevel = args['--loglevel']
    _setup_logging(loglevel=loglevel)
    logger = logging.getLogger('casper')

    # parse arguments
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

    state_file = args['--state-file']
    root_dir = args['--root-dir']

    exclude_dirs = args['--exclude-dirs']
    if exclude_dirs:
        exclude_dirs = set(exclude_dirs.split(","))

    exclude_state_res = args['--exclude-state-res']
    if exclude_state_res:
        exclude_state_res = set(exclude_state_res.split(","))

    services = args['--services']
    if services:
        svc_list = services.split(",")
        services = [s for s in svc_list if s in SUPPORTED_SERVICES]

        if len(services) < len(svc_list):
            logger.warning("Ignoring one or more unsupported services")

        services = set(services)
    else:
        services = SUPPORTED_SERVICES

    exclude_cloud_res = args['--exclude-cloud-res']
    if exclude_cloud_res:
        exclude_cloud_res = set(exclude_cloud_res.split(","))

    rebuild = args['--rebuild']
    detailed = args['--detailed']
    output_file = args['--output-file']

    if rebuild:
        build_command = True

    casper = Casper(
        bucket_name,
        start_directory=root_dir,
        state_file=state_file,
        profile=aws_profile,
        exclude_resources=exclude_cloud_res,
        load_state=not build_command
    )

    if build_command:
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

        if len(services) == 0:
            logger.warning("No supported service specified")

        for svc in services:
            svc_ghost[svc] = casper.scan(service_name=svc, detailed=detailed)

        print("")
        for svc in services:
            print(svc.upper())
            print("--------------------------------------------------------")
            for key in svc_ghost[svc].keys():
                count = svc_ghost[svc][key]['count']
                if count > 0:
                    print(f"{count} ghost {key} found")
            print("")

        if output_file:
            with open(output_file, 'w') as fid:
                fid.write(
                    json.dumps(
                        svc_ghost, indent=4, sort_keys=True, default=str
                    )
                )

            print("--------------------------------------------------------")
            print(
                f"Full result written to "
                f"{os.path.join(os.getcwd(), output_file)}"
            )


if __name__ == '__main__':
    cli()
