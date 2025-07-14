import boto3
import json
import base64
import time

region = "ap-south-1"
ec2 = boto3.client("ec2", region_name=region)
elbv2 = boto3.client("elbv2", region_name=region)
autoscaling = boto3.client("autoscaling", region_name=region)
iam = boto3.client("iam")
ec2_resource = boto3.resource("ec2", region_name=region)

TAG_PREFIX = "ankit-anand-monday"
KEY_NAME = "AnkitAnandHeroViredB10"
AMI_ID = "ami-0f918f7e67a3323f0"
INSTANCE_TYPE = "t2.micro"
BACKEND_IMAGE_1 = "975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/backendhelloservice"
BACKEND_IMAGE_2 = "975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/backendprofileservice"
FRONTEND_IMAGE = "975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/frontend"


def find_resource_by_tag(resource_type, tag_key, tag_value):
    filters = [{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
    if resource_type == "vpc":
        vpcs = ec2.describe_vpcs(Filters=filters).get("Vpcs", [])
        return vpcs[0] if vpcs else None
    if resource_type == "subnet":
        return ec2.describe_subnets(Filters=filters).get("Subnets", [])
    if resource_type == "igw":
        igws = ec2.describe_internet_gateways(Filters=filters).get("InternetGateways", [])
        return igws[0] if igws else None
    if resource_type == "sg":
        sgs = ec2.describe_security_groups(Filters=filters).get("SecurityGroups", [])
        return sgs[0] if sgs else None
    return None


# -------------------------------
# 1. VPC
# -------------------------------
vpc = find_resource_by_tag("vpc", "Name", f"{TAG_PREFIX}-vpc")
if not vpc:
    print("Creating VPC...")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]
    vpc_id = vpc["VpcId"]
    ec2.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": f"{TAG_PREFIX}-vpc"}])
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})
else:
    vpc_id = vpc["VpcId"]
    print(f"VPC exists: {vpc_id}")

# -------------------------------
# 2. Subnets
# -------------------------------
def find_subnet_by_cidr(vpc_id, cidr):
    subnets = ec2.describe_subnets(Filters=[
        {'Name': 'vpc-id', 'Values': [vpc_id]}
    ])["Subnets"]
    for subnet in subnets:
        if subnet["CidrBlock"] == cidr:
            return subnet
    return None

subnet_ids = []
cidr_blocks = ["10.0.1.0/24", "10.0.2.0/24"]
for i, cidr in enumerate(cidr_blocks):
    subnet = find_subnet_by_cidr(vpc_id, cidr)
    if subnet:
        print(f"Subnet {cidr} already exists: {subnet['SubnetId']}")
        subnet_ids.append(subnet["SubnetId"])
    else:
        az = f"{region}{chr(97 + i)}"  # ap-south-1a, ap-south-1b
        new_subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az)["Subnet"]
        ec2.create_tags(Resources=[new_subnet["SubnetId"]], Tags=[{"Key": "Name", "Value": f"{TAG_PREFIX}-subnet"}])
        subnet_ids.append(new_subnet["SubnetId"])
        print(f"Created new subnet {cidr}: {new_subnet['SubnetId']}")

for subnet_id in subnet_ids:
    ec2.modify_subnet_attribute(
        SubnetId=subnet_id,
        MapPublicIpOnLaunch={"Value": True}
    )


# -------------------------------
# 3. Internet Gateway
# -------------------------------
def get_attached_igw(vpc_id):
    igws = ec2.describe_internet_gateways()["InternetGateways"]
    for igw in igws:
        for attach in igw.get("Attachments", []):
            if attach["VpcId"] == vpc_id and attach["State"] == "available":
                return igw
    return None

igw = get_attached_igw(vpc_id)
if igw:
    igw_id = igw["InternetGatewayId"]
    print(f"Internet Gateway already attached: {igw_id}")
else:
    print("Creating and attaching Internet Gateway...")
    igw = ec2.create_internet_gateway()["InternetGateway"]
    igw_id = igw["InternetGatewayId"]
    ec2.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw_id)
    ec2.create_tags(Resources=[igw_id], Tags=[{"Key": "Name", "Value": f"{TAG_PREFIX}-igw"}])

# -------------------------------
# 4. Route Table
# -------------------------------
rts = ec2.describe_route_tables(Filters=[
    {'Name': 'vpc-id', 'Values': [vpc_id]}
])["RouteTables"]
rt_id = rts[0]["RouteTableId"]
try:
    ec2.create_route(RouteTableId=rt_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
except:
    pass  # Route might already exist
for subnet_id in subnet_ids:
    ec2.associate_route_table(RouteTableId=rt_id, SubnetId=subnet_id)

# -------------------------------
# 5. Security Group
# -------------------------------
sg = find_resource_by_tag("sg", "Name", f"{TAG_PREFIX}-sg")
if not sg:
    print("Creating Security Group...")
    sg = ec2.create_security_group(
        GroupName=f"{TAG_PREFIX}-sg",
        Description="Allow SSH, frontend and backend",
        VpcId=vpc_id
    )
    sg_id = sg["GroupId"]
    ec2.create_tags(Resources=[sg_id], Tags=[{"Key": "Name", "Value": f"{TAG_PREFIX}-sg"}])
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": p, "ToPort": p, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
            for p in [22, 3000, 3001, 3002]
        ]
    )
else:
    sg_id = sg["GroupId"]
    print(f"Security Group exists: {sg_id}")

# -------------------------------
# 6. IAM Role and Instance Profile
# -------------------------------
role_name = f"{TAG_PREFIX}-ec2-role"
try:
    iam.get_role(RoleName=role_name)
except iam.exceptions.NoSuchEntityException:
    print("Creating IAM Role and Instance Profile...")
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
    iam.attach_role_policy(RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly")
    iam.create_instance_profile(InstanceProfileName=role_name)
    iam.add_role_to_instance_profile(InstanceProfileName=role_name, RoleName=role_name)
    time.sleep(10)

# -------------------------------
# 7. ALB and Target Group
# -------------------------------
lbs = elbv2.describe_load_balancers(Names=[f"{TAG_PREFIX}-alb"])["LoadBalancers"] if elbv2.describe_load_balancers()["LoadBalancers"] else []
if lbs:
    lb = lbs[0]
    lb_arn = lb["LoadBalancerArn"]
    lb_dns = lb["DNSName"]
else:
    lb = elbv2.create_load_balancer(
        Name=f"{TAG_PREFIX}-alb",
        Subnets=subnet_ids,
        SecurityGroups=[sg_id],
        Scheme="internet-facing",
        Type="application",
        IpAddressType="ipv4"
    )["LoadBalancers"][0]
    lb_arn = lb["LoadBalancerArn"]
    lb_dns = lb["DNSName"]

tg = elbv2.create_target_group(
    Name=f"{TAG_PREFIX}-tg",
    Protocol="HTTP",
    Port=3001,
    VpcId=vpc_id,
    TargetType="instance",
    HealthCheckPath="/"
)["TargetGroups"][0]
tg_arn = tg["TargetGroupArn"]

try:
    elbv2.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol="HTTP",
        Port=3001,
        DefaultActions=[{"Type": "forward", "TargetGroupArn": tg_arn}]
    )
except elbv2.exceptions.DuplicateListenerException:
    pass

# -------------------------------
# 8. Launch Template for Backend
# -------------------------------
backend_user_data = f"""#!/bin/bash
yum update -y
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user
$(aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin 975050024946.dkr.ecr.{region}.amazonaws.com)
docker run -d -p 3001:3001 {BACKEND_IMAGE_1}
docker run -d -p 3002:3002 {BACKEND_IMAGE_2}
"""

lt_name = f"{TAG_PREFIX}-lt"
try:
    lt = ec2.create_launch_template(
    LaunchTemplateName=lt_name,
    LaunchTemplateData={
        "ImageId": AMI_ID,
        "InstanceType": INSTANCE_TYPE,
        "KeyName": KEY_NAME,
        "NetworkInterfaces": [{
            "AssociatePublicIpAddress": True,
            "DeviceIndex": 0,
            "SubnetId": subnet_ids[0],
            "Groups": [sg_id]
        }],
        "UserData": base64.b64encode(backend_user_data.encode()).decode(),
        "IamInstanceProfile": {"Name": role_name}
    }
)["LaunchTemplate"]
    lt_id = lt["LaunchTemplateId"]
except ec2.exceptions.ClientError as e:
    lt_id = ec2.describe_launch_templates(LaunchTemplateNames=[lt_name])["LaunchTemplates"][0]["LaunchTemplateId"]

# -------------------------------
# 9. Auto Scaling Group for Backend
# -------------------------------
asg_name = f"{TAG_PREFIX}-asg"
existing_asgs = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])["AutoScalingGroups"]
if not existing_asgs:
    autoscaling.create_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchTemplate={"LaunchTemplateId": lt_id, "Version": "$Latest"},
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=1,
        VPCZoneIdentifier=",".join(subnet_ids),
        TargetGroupARNs=[tg_arn],
        Tags=[{"Key": "Name", "Value": f"{TAG_PREFIX}-backend", "PropagateAtLaunch": True}]
    )

# -------------------------------
# 10. Launch Frontend EC2
# -------------------------------
frontend_user_data = f"""#!/bin/bash
yum update -y
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user
$(aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin 975050024946.dkr.ecr.{region}.amazonaws.com)
docker run -d -p 3000:3000 -e REACT_APP_BACKEND_URL=http://{lb_dns}:3001 {FRONTEND_IMAGE}
"""

instances = ec2_resource.instances.filter(
    Filters=[{"Name": "tag:Name", "Values": [f"{TAG_PREFIX}-frontend"]}]
)
if not list(instances):
    ec2_resource.create_instances(
    ImageId=AMI_ID,
    InstanceType=INSTANCE_TYPE,
    KeyName=KEY_NAME,
    MinCount=1,
    MaxCount=1,
    NetworkInterfaces=[{
        "DeviceIndex": 0,
        "AssociatePublicIpAddress": True,
        "SubnetId": subnet_ids[0],
        "Groups": [sg_id]
    }],
    UserData=frontend_user_data,
    IamInstanceProfile={"Name": role_name},
    TagSpecifications=[{
        "ResourceType": "instance",
        "Tags": [{"Key": "Name", "Value": f"{TAG_PREFIX}-frontend"}]
    }]
)


print("✅ Infrastructure setup complete.")
