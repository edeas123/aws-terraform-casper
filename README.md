# Casper
A tool for detecting ghost resources running on your AWS cloud environment.

## Features

## Usage

| Argument        | Description |
| ------------- |:-------------|
| -h, --help | Display help message and exit |
| --root-dir | The root terraform directory |
| --aws-profile | AWS profile to use |
| --bucket-name-prefix | Prefix for bucket name created to save and retrieve state |
| --exclude-dirs | Comma separated list of directories to ignore |
| --exclude-state-res | Comma separated list of terraform state resources to ignore |
| --service | Comma separated list of services to scan, default is to scan all supported services |
| --exclude-cloud-res | Comma separated list of resources ids to ignore |
| --rebuild | Rebuild and save state first before scanning |
| --summary-only | Print only the counts results |
| --log-to | Filename to send logs, ignore if logs should be sent to stdout |
| --output-file | Output full result to specified file |

## Usage Examples

```
casper build --root-dir=. --aws-profile=casper_profile

---------------------------------------

1 state(s) discovered
1 supported resource group(s) collected
1 resource(s) saved to bucket

```

## Requirements


## License

[Mozilla Public License v2.0](LICENSE)
