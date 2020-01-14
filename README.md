# Casper
[![CircleCI](https://circleci.com/gh/edeas123/aws-terraform-casper.svg?style=svg&circle-token=5115202ddbba134358fefd5b36e34857cc2bbfe0)](https://circleci.com/gh/edeas123/aws-terraform-casper)

Casper is a tool for detecting ghost resources running on your AWS cloud environment.

## Features

Some of the benefits Casper provides includes:
* Security and resource management: Ghosts in your infrastructure can be a 
sign of a security exploit because the resources were not provisioned 
through the traditional means used in your organization.
* Coverage: It would help to measure coverage for an organization gradually using 
Terraform to provision their AWS infrastructure.

## Installation

Do the following to install Casper:
```
git clone https://github.com/edeas123/aws-terraform-casper.git
pip install -r requirements.txt
```

## Requirements

Casper was tested with the following minimum IAM permission:

## Environment Variable

The following environment variable should be set:

| Variable        | Description |
| ------------- |:-------------|
| AWS_PROFILE | [Optional] If the `--aws-profile` argument is not passed, the call to terraform uses the aws profile specified in this variable, otherwise the default aws profile is used|
| CASPER_BUCKET | The bucket to save state in. If this variable is not specified, Casper would prompt for a bucket name. It could also be passed using the `--bucket-name` argument |

## Usage

| Argument        | Description |
| ------------- |:-------------|
| -h, --help | Display help message and exit |
| --root-dir | The root terraform directory |
| --aws-profile | AWS profile to use. If not set, uses the value in AWS_PROFILE environment variable |
| --bucket-name | Bucket name created to save and retrieve state. If not set, uses the value in CASPER_BUCKET environment variable |
| --exclude-dirs | Comma separated list of directories to ignore |
| --exclude-state-res | Comma separated list of terraform state resources to ignore |
| --service | Comma separated list of services to scan, default is to scan all supported services |
| --exclude-cloud-res | Comma separated list of resources ids to ignore |
| --rebuild | Rebuild and save state first before scanning |
| --summary-only | Print only the counts results |
| --log-to | Filename to send logs, ignore if logs should be sent to stdout |
| --output-file | Output full result to specified file |

## Example

Casper `BUILD` collects and stores information about the infrastructure
captured in terraform. Casper collects the ID of all the resources and stores it in `CASPER_BUCKET`.

```
$ python casper.py build --root-dir=/Users/username/terraform_dev_dir --aws-profile=casper_profile

Terraform
--------------------------------------------
14 state(s) checked
3 supported resource group(s) discovered
21 resource(s) saved to bucket

```

Casper `SCAN` compares the resources on terraform with that running in the cloud, and returns the summary and 
details of all the resources found in the cloud but not captured in terraform. SCAN uses the terraform information that was
saved to `CASPER_BUCKET` or it rebuilds that information (if the `--rebuild` argument is set)

```
$ python casper.py scan --rebuild --root-dir=/Users/username/terraform_dev_dir --aws-profile=casper_profile

Terraform
--------------------------------------------------------
4 state(s) checked
4 supported resource group(s) discovered
7 resource(s) saved to bucket

EC2
--------------------------------------------------------
1 ghost aws_instance found
3 ghost aws_autoscaling_group found
1 ghost aws_security_group found

S3
--------------------------------------------------------
1 ghost aws_s3_bucket found

```

## Contributing

Contributions to the development of Casper is very much welcomed. You can contribute in the following ways:

1. Fix coverage of a particular resource. For example, are there ways an aws instance can be created directly or indirectly
in terraform that is not covered. Currently we support instances created through `aws_spot_instance` and `aws_instance`.

2. Support coverage for other services.

3. Support other resources within a service. Do you think an important resource is not supported. You can contribute code to support that
resource.


Any other forms of contribution is also welcome.

## License

[Mozilla Public License v2.0](LICENSE)
