import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
from constructs import Construct

class NetworkStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(self, "VPC",
                           max_azs=2,
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   cidr_mask=24,
                                   name="PublicSubnet",
                                   subnet_type=ec2.SubnetType.PUBLIC,
                               ),
                               ec2.SubnetConfiguration(
                                   cidr_mask=24,
                                   name="PrivateSubnet",
                                   subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                               )
                           ])