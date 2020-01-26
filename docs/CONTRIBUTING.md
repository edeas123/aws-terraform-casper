## Contributing

You can contribute in the following ways:

1. Support coverage of more services.

2. Support more resources within a service.

3. Improve coverage of a particular resource. For example, are there other ways an aws instance can be created directly or indirectly in terraform. Currently we support instances created through `aws_spot_instance` and `aws_instance`.

4. Improve documentation, report bugs, add tests and more. Any other forms of contribution is also appreciated.

### Support a new service

AWS has several services and new ones are regularly added. Follow these steps to contribute code to add support for a new service.

1. Add a new service module in the casper/service directory. The service module should contain a class (appropriately named e.g for EC2 service, the class name was EC2Service) and inherit from BaseService.

2. At minimum, the class should implement the scan_service method. In most cases, using `pass` is sufficient. 
The purpose of the function is to support cases where multiple resources depends on eachother very closely. If you need to update the ghosts found for one resource type using details of ghosts found on another resource type within a service, this is the function to do so. For example, in the case of the EC2 service, ghost aws_instances came from diff between aws_instances 
(and aws_spot_instances) on terraform and aws_nstance (excluding those which are part of an autoscaling group) on AWS, 
as well as aws_instances attached to ghost aws_auto_scaling_group. 

3. Additional methods can now be written in this format `_get_live_<resource_group>` and should return a dictionary with the resource id as key, and the resource data (as returned by AWS) as value. For each resource group supported, include it in the `_resources_groups` instance variable.

4. In the aws module in the states directory, add a new method to the AWSState class. The method should be named in this format `_get_state_<resource_group>`, it should take a single string field and return `self._get_field(<field>, text)` where field is the field used for the resource id in the terraform state. Usually, this field is either `id` or `name`.

5. If the field in 4 above is anything other than `id` or `name` add a test for that field to ensure the regex in the `_get_field` function returns the correct result for that field.

6. If terraform supports two names for the same resource (e.g `aws_lb` and `aws_alb`) or you just want to group the resource together, you can do that using the `_resource_group_remap` instance variable.

7. In the BaseService class, updated `SUPPORTED_SERVICES` constant to include the new service.

8. Add tests for your service following the same format as the other service tests.
