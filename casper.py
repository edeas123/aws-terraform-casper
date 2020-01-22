"""
Casper.

Usage:
    casper.py build [--root-dir=<dir> --bucket-name=<bn> --state-file=<sf> --aws-profile=<profile> --exclude-dirs=<ed> --exclude-state-res=<esr>]
    casper.py scan  [--root-dir=<dir> --bucket-name=<bn> --state-file=<sf> --aws-profile=<profile> --service=<svc> --exclude-cloud-res=<ecr> --rebuild --detailed --output-file=<f>]
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
    --service=<svc>                         Comma separated list of services to scan, default is to scan all supported services.
    --exclude-cloud-res=<ecr>               Comma separated list of resources ids to ignore.
    --rebuild                               Rebuild and save state first before scanning.
    --detailed                              Retrieve and include details about the resources discovered through scan.
    --output-file=<f>                       Output full result to specified file.

"""  # noqa

from docopt import docopt
from casper.main import run


if __name__ == '__main__':
    args = docopt(__doc__)
    run(args)
