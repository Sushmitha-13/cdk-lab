from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    core
)
from constructs import Construct

class CdkCloudFormationStack(Stack):

    @property
    def vpc(self):
        return self.cdk_lab_vpc
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        # Define the VPC
        vpc = ec2.Vpc(
            self, "cdk_vpc",
            cidr="10.0.0.0/18",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet1",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PublicSubnet2",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
                ]
            )
        
        # Internet Gateway
        igw = ec2.CfnInternetGateway(self, "InternetGateway")

        # Attach Gateway to VPC
        ec2.CfnVPCGatewayAttachment(
            self, 
            "AttachGateway",
            vpc_id=vpc.vpc_id,
            internet_gateway_id=igw.ref
            )
        
        # Route Table 
        route_table = ec2.CfnRouteTable(
            self, 
            "RouteTable",
            vpc_id=vpc.vpc_id
            )
        
        ec2.CfnRoute(
            self, 
            "PublicRoute",
            route_table_id=route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=igw.ref
            )
        
        # Security Group
        sg = ec2.SecurityGroup(
            self, 
            "WebserversSG",
            vpc=vpc,
            description="Security group for web servers",
            allow_all_outbound=True
            )
        
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))

        # EC2 Instances
        ami_id = "ami-086f060214da77a16"
        instance_type = ec2.InstanceType("t2.micro")

        web_server1 = ec2.Instance(
            self, 
            "WebServerInstance1",
            instance_type=instance_type,
            machine_image=ec2.MachineImage.generic_linux({"us-east-1": ami_id}),
            vpc=vpc,
            key_name="KeyPair",
            security_group=sg
            )

        web_server2 = ec2.Instance(
            self, 
            "WebServerInstance2",
            instance_type=instance_type,
            machine_image=ec2.MachineImage.generic_linux({"us-east-1": ami_id}),
            vpc=vpc,
            key_name="KeyPair",
            security_group=sg
            )
        

        # Load Balancer
        lb = elb.ApplicationLoadBalancer(self, "EngineeringLB",
                                           vpc=vpc,
                                           internet_facing=True)
        listener = lb.add_listener("Listener80", port=80)
        
        target_group = elb.ApplicationTargetGroup(self, "EngineeringWebServers",
                                                    port=80,
                                                    vpc=vpc,
                                                    target_type=elb.TargetType.INSTANCE)
        
        listener.add_targets("TargetGroup", port=80, targets=[web_server1, web_server2])

        # Output Load Balancer DNS
        core.CfnOutput(self, "LoadBalancerDNS", value=lb.load_balancer_dns_name)