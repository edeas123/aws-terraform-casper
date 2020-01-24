# Casper
[![CircleCI](https://circleci.com/gh/edeas123/aws-terraform-casper.svg?style=svg&circle-token=5115202ddbba134358fefd5b36e34857cc2bbfe0)](https://circleci.com/gh/edeas123/aws-terraform-casper)

Casper is a tool for detecting `ghosts` running on your AWS cloud environment. Ghosts are resources running on your cloud 
environment but not provisioned through infrastructure as code (IaC) tools such as Terraform. Casper currently works only with AWS and Terraform.

## Benefits

Some of the benefits Casper provides includes:
* **Security and resource management**: Ghosts in your infrastructure can be a sign of a security exploit because the resources were not provisioned through the traditional means used in your organization.

* **Coverage**: It would help to measure coverage for an organization gradually using 
Terraform to provision their AWS infrastructure. Running Casper on an empty terraform state directory would detect all the (supported) resources in your cloud as ghosts. Then you can gradually import those resources to terraform and improve coverage.

## Installation

Do the following to install Casper:
```
git clone https://github.com/edeas123/aws-terraform-casper.git
cd aws-terraform-casper
pip install -r requirements.txt
```

## Requirements

Casper requires general READ permissions to use terraform in refreshing and listing the states. It also requires permission to READ and WRITE to S3 (particularly the `CASPER_BUCKET` bucket) where it saves and loads the state resource IDs.

## Environment Variable

The following environment variable should be set:

| Variable        | Description |
| ------------- |:-------------|
| AWS_PROFILE | [Optional] If the `--aws-profile` argument is not passed, the call to terraform uses the aws profile specified in this variable, otherwise your default aws profile is used|
| CASPER_BUCKET | The bucket to save state resource ids. If this variable is not specified, Casper would prompt for a bucket name. It could also be passed using the `--bucket-name` argument |

## Usage

| Argument        | Description |
| ------------- |:-------------|
| -h, --help | Display help message and exit |
| --root-dir | The root terraform directory |
| --aws-profile | AWS profile to use. If not set, uses the value in AWS_PROFILE environment variable |
| --bucket-name | Bucket name created to save and retrieve state. If not set, uses the value in CASPER_BUCKET environment variable |
| --exclude-dirs | Comma separated list of directories to ignore |
| --exclude-state-res | Comma separated list of terraform state resources to ignore |
| --services | Comma separated list of services to scan, the default is to scan all supported services |
| --exclude-cloud-res | Comma separated list of cloud resources ids to ignore |
| --rebuild | Rebuild and save state first before scanning |
| --detailed | Retrieve and include details about the resources discovered through scan |
| --output-file | Output detailed result to specified file |
| --loglevel | Log level. Defaults to INFO if unspecified |

## Example

Casper `BUILD` collects and stores information about the infrastructure captured in terraform. Casper collects the IDs of all the state resources and stores it in `CASPER_BUCKET`.

```
$ python casper.py build --root-dir=/Users/username/terraform_dev_dir --aws-profile=casper_profile
```

```
Terraform
--------------------------------------------
4 state(s) checked
4 supported resource group(s) discovered
7 resource(s) saved to bucket

```

Casper `SCAN` compares the resources on terraform with that running in the cloud, and returns the summary and details of all the resources found in the cloud but not captured in terraform. SCAN uses the terraform state information that was saved to `CASPER_BUCKET` or it rebuilds that information (if the `--rebuild` argument is set)

```
$ python casper.py scan
```

```
EC2
--------------------------------------------------------
1 ghost aws_instance found
3 ghost aws_autoscaling_group found
1 ghost aws_security_group found

S3
--------------------------------------------------------
1 ghost aws_s3_bucket found

```

```
$ python casper.py scan  --output-file result.json
```
```
EC2
--------------------------------------------------------
1 ghost aws_instance found
3 ghost aws_autoscaling_group found
1 ghost aws_security_group found

S3
--------------------------------------------------------
1 ghost aws_s3_bucket found

--------------------------------------------------------
Full result written to /Users/username/aws-terraform-casper/result.json
```
Syntax for the full result is:
```yaml
{
  "<service>" : {
    "<resource_group>": {
      "count": int, # The number of ghost resources found
      "ids": [
        "string"  # The ids of the ghost resources found
      ],
      "resources": [
        "dict"  # Details of each resources as returned by AWS. Only shown if `--detailed` flag is set
      ]
    } 
  }
}
```
An example full result (without `--detailed` flag) is shown below.

```yaml
{
    "ec2": {
        "aws_alb": {
            "count": 4,
            "ids": [
                "core-service-alb",
                "01af4240-someservice-7d55",
                "752a14ce-someotherserice-7d55",
                "01af4240-kubernetesdashboa-2415"
            ]
        },
        "aws_autoscaling_group": {
            "count": 3,
            "ids": [
                "core-infra-asg",
                "core-dev-asg",
                "core-prod-asg"
            ]
        },
        "aws_elb": {
            "count": 1,
            "ids": [
                "our_new_elb"
            ]
        },
        "aws_instance": {
            "count": 2,
            "ids": [
                "i-084699b83473e2c69",
                "i-0101522650aeaa2dd"
            ]
        },
        "aws_security_group": {
            "count": 1,
            "ids": [
                "sg-03ed7e004de2235bd"
            ]
        }
    },
    "iam": {
        "aws_iam_role": {
            "count": 4,
            "ids": [
                "AWSServiceRoleForTrustedAdvisor",
                "AWSServiceRoleForAmazonGuardDuty",
                "AWSServiceRoleForElastiCache",
                "casper-role"
            ]
        },
        "aws_iam_user": {
            "count": 1,
            "ids": [
                "user.me"
            ]
        }
    },
    "s3": {
        "aws_s3_bucket": {
            "count": 2,
            "ids": [
                "fake_ghost_bucket",
                "temp_bucket_delete_later"
            ]
        }
    }
}
```

## Contributing

Contributions to the development of Casper is very much welcome. You can contribute in the following ways:

1. Fix coverage of a particular resource. For example, are there other ways an aws instance can be created directly or indirectly in terraform. Currently we support instances created through `aws_spot_instance` and `aws_instance`.

2. Support coverage for other services. Currently we support EC2, IAM, S3. Extending to support other services is straightforward.

3. Support other resources within a service. Do you think an important service resource is not supported? You can contribute code to support that resource.

4. More detailed documentations on how to contribute, for example how to add a new service.


Any other forms of contribution is also appreciated.

## License

[Mozilla Public License v2.0](LICENSE)
