import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
import aws_cdk.aws_elasticloadbalancingv2_targets as elbv2_targets

from constructs import Construct


class CdkalbStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "EngineeringVpc",
                      cidr="10.0.0.0/18",
                      max_azs=2,
                      subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   cidr_mask=24,
                                   name="PublicSubnet1",
                                   subnet_type=ec2.SubnetType.PUBLIC,
                               ),
                               ec2.SubnetConfiguration(
                                   cidr_mask=24,
                                   name="PublicSubnet2",
                                   subnet_type=ec2.SubnetType.PUBLIC,
                               )
                      ])

        # Security Group
        sg = ec2.SecurityGroup(self, "WebServerSG",
                               vpc=vpc,
                               description="Security group for web server",
                               allow_all_outbound=True)
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))

        # IAM Role and Instance Profile for EC2
        role = iam.Role(self, "WebInstanceRole",
                        assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                        managed_policies=[
                            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                            iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
                        ])

        instance_profile = iam.CfnInstanceProfile(self, "WebInstanceProfile",
                                                  roles=[role.role_name])

        user_data = ec2.UserData.for_linux()
        user_data.add_commands("yum update -y",
                                "yum install -y git httpd php",
                                "service httpd start",
                                "chkconfig httpd on",
                                "aws s3 cp s3://seis665-public/index.php /var/www/html/")
        subnets = vpc.public_subnets
        # EC2 Instances
        keyname = "web"
        instance1 = ec2.Instance(self, "web1",
                                instance_type=ec2.InstanceType("t2.micro"),
                                machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                vpc=vpc,
                                security_group=sg,
                                key_name=keyname,
                                role=role,
                                user_data=user_data,
                                vpc_subnets=ec2.SubnetSelection(subnets=[subnets[0]]))
        
        instance2 = ec2.Instance(self, "web2",
                                instance_type=ec2.InstanceType("t2.micro"),
                                machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2), 
                                vpc=vpc,
                                security_group=sg,
                                key_name=keyname,
                                role=role,
                                user_data=user_data,
                                vpc_subnets=ec2.SubnetSelection(subnets=[subnets[1]]))

        # Application Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "EngineeringLB",
                                           vpc=vpc,
                                           internet_facing=True,
                                           vpc_subnets=ec2.SubnetSelection(subnets=vpc.public_subnets))
        
        listener = lb.add_listener("Listener", port=80)
        

        instance_target1 = elbv2_targets.InstanceTarget(instance1, 80)
        instance_target2 = elbv2_targets.InstanceTarget(instance2, 80)

        target_group = listener.add_targets("TargetGroup",
                                            port=80,
                                            targets=[instance_target1, instance_target2])
        

    