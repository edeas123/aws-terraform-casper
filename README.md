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

Install Casper by running:
```
pip install aws-terraform-casper
```

## Usage

Run Casper using:

`casper <sub_command> [options]`

Casper currently has two subcommands: `BUILD` and `SCAN`.

| Subcommand        | Description |
| ------------- |:-------------|
| build | Collects and stores information about the infrastructure captured in terraform. |
| scan | Compares the resources on terraform with that running in the cloud. |

Casper currently supports the following options:

| Options        | Description |
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

Refer to the [usage guide](./docs/guide.md) for examples, results format and how to use Casper from your code.


## Contributing

Contributions to the development of Casper is very much welcome. Please refer to [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for details on ways to contribute.


## License

[Mozilla Public License v2.0](LICENSE)
