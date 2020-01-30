## Requirements

Casper requires an AWS_PROFILE with READ permissions to use terraform in refreshing and listing the states. 
By default it uses the local machine's default AWS profile. 

If you specify the `CASPER_BUCKET` environment variable or use the `--bucket-name` option, 
then the AWS_PROFILE must also have READ and WRITE permissions to that bucket else Casper would
revert to saving the casper state in the current directory.


## Example

Casper currently has two subcommands: BUILD and SCAN.

Casper `BUILD` collects and stores information about the infrastructure captured in terraform. Casper collects the IDs of all the state resources and stores it in `CASPER_BUCKET`.

```shell script
casper build --root-dir=/Users/username/terraform_dev_dir --aws-profile=casper_profile
```

```
Terraform
--------------------------------------------
4 state(s) checked
4 supported resource group(s) discovered
7 resource(s) saved to bucket

```

Casper `SCAN` compares the resources on terraform with that running in the cloud, and returns the summary and details of all the resources found in the cloud but not captured in terraform. SCAN uses the terraform state information that was saved to `CASPER_BUCKET` or it rebuilds that information (if the `--rebuild` argument is set)

```shell script
casper scan
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

```shell script
casper scan  --output-file result.json
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
## Library

Casper can also be used as a library. To use Casper from your code:

```python
# import into your code
from casper import Casper

# create an instance of Casper
casper = Casper()

# Casper Build
state_summary = casper.build()

# Casper Scan
svc = "ec2" # requires one positional argument for the service to scan e.g. ec2
ghosts_resources = casper.scan(svc) 

```
The syntax for the result (`ghost_resources`) from Casper Scan is:
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
