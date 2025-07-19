import boto3
import base64

region = "ap-south-1"

# Resource names
VPC_NAME = "ankit-vpc"
SUBNET1_NAME = "ankit-subnet-1a"
SUBNET2_NAME = "ankit-subnet-1b"
IGW_NAME = "ankit-igw"
RT_NAME = "ankit-route-table"
SG_NAME = "ankit-sg"
ALB_HELLO_NAME = "ankit-alb-hello"
ALB_PROFILE_NAME = "ankit-alb-profile"
TG_HELLO_NAME = "ankit-tg-hello"
TG_PROFILE_NAME = "ankit-tg-profile"
ASG_BACKEND_NAME = "ankit-asg-backend"
LT_BACKEND_NAME = "ankit-lt-backend"
FRONTEND_NAME = "ankit-frontend"

# ECR Images
BACKEND_HELLO_IMG = "975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/backendhelloservice:latest"
BACKEND_PROFILE_IMG = "975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/backendprofileservice:latest"
FRONTEND_IMG = "975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/frontend:latest"

# EC2 Specs
AMI_ID = "ami-0f918f7e67a3323f0"
INSTANCE_TYPE = "t3.micro"
KEY_NAME = "AnkitAnandHeroViredB10"
IAM_INSTANCE_PROFILE = "ankit-ecr-pull-ec2"
MONGO_URL = "mongodb+srv://ankit_200193:dwg2Cb4278nAqAEI@cluster0.ou9e6.mongodb.net/MERNapp"

# Boto3 clients
ec2 = boto3.client('ec2', region_name=region)
elbv2 = boto3.client('elbv2', region_name=region)
autoscaling = boto3.client('autoscaling', region_name=region)


# -------- Helper Function --------
def get_resource_by_name(resource_type, name):
    if resource_type == 'vpc':
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [name]}])['Vpcs']
        return vpcs[0] if vpcs else None
    elif resource_type == 'subnet':
        subnets = ec2.describe_subnets(Filters=[{'Name': 'tag:Name', 'Values': [name]}])['Subnets']
        return subnets[0] if subnets else None
    elif resource_type == 'igw':
        igws = ec2.describe_internet_gateways(Filters=[{'Name': 'tag:Name', 'Values': [name]}])['InternetGateways']
        return igws[0] if igws else None
    elif resource_type == 'route-table':
        rts = ec2.describe_route_tables(Filters=[{'Name': 'tag:Name', 'Values': [name]}])['RouteTables']
        return rts[0] if rts else None
    elif resource_type == 'sg':
        sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [name]}])['SecurityGroups']
        return sgs[0] if sgs else None
    elif resource_type == 'launch-template':
        lts = ec2.describe_launch_templates(Filters=[{'Name': 'launch-template-name', 'Values': [name]}])['LaunchTemplates']
        return lts[0] if lts else None
    elif resource_type == 'alb':
        albs = elbv2.describe_load_balancers()['LoadBalancers']
        for alb in albs:
            if alb['LoadBalancerName'] == name:
                return alb
        return None
    elif resource_type == 'target-group':
        tgs = elbv2.describe_target_groups()['TargetGroups']
        for tg in tgs:
            if tg['TargetGroupName'] == name:
                return tg
        return None
    elif resource_type == 'asg':
        asgs = autoscaling.describe_auto_scaling_groups()['AutoScalingGroups']
        for asg in asgs:
            if asg['AutoScalingGroupName'] == name:
                return asg
        return None


# -------- VPC and Networking --------
def create_vpc_and_network():
    vpc = get_resource_by_name('vpc', VPC_NAME)
    if not vpc:
        vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
        vpc_id = vpc['Vpc']['VpcId']
        ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': VPC_NAME}])
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        print(f"Created VPC: {vpc_id}")
    else:
        vpc_id = vpc['VpcId']
        print(f"Using existing VPC: {vpc_id}")

    subnet1 = get_resource_by_name('subnet', SUBNET1_NAME)
    if not subnet1:
        subnet1 = ec2.create_subnet(VpcId=vpc_id, CidrBlock='10.0.1.0/24', AvailabilityZone=f'{region}a')
        ec2.create_tags(Resources=[subnet1['Subnet']['SubnetId']], Tags=[{'Key': 'Name', 'Value': SUBNET1_NAME}])
        ec2.modify_subnet_attribute(SubnetId=subnet1['Subnet']['SubnetId'], MapPublicIpOnLaunch={'Value': True})
        print(f"Created Subnet1: {subnet1['Subnet']['SubnetId']}")
    else:
        subnet1 = {'Subnet': subnet1}
        print(f"Using existing Subnet1: {subnet1['Subnet']['SubnetId']}")

    subnet2 = get_resource_by_name('subnet', SUBNET2_NAME)
    if not subnet2:
        subnet2 = ec2.create_subnet(VpcId=vpc_id, CidrBlock='10.0.2.0/24', AvailabilityZone=f'{region}b')
        ec2.create_tags(Resources=[subnet2['Subnet']['SubnetId']], Tags=[{'Key': 'Name', 'Value': SUBNET2_NAME}])
        ec2.modify_subnet_attribute(SubnetId=subnet2['Subnet']['SubnetId'], MapPublicIpOnLaunch={'Value': True})
        print(f"Created Subnet2: {subnet2['Subnet']['SubnetId']}")
    else:
        subnet2 = {'Subnet': subnet2}
        print(f"Using existing Subnet2: {subnet2['Subnet']['SubnetId']}")

    igw = get_resource_by_name('igw', IGW_NAME)
    if not igw:
        igw = ec2.create_internet_gateway()
        ec2.create_tags(Resources=[igw['InternetGateway']['InternetGatewayId']], Tags=[{'Key': 'Name', 'Value': IGW_NAME}])
        ec2.attach_internet_gateway(InternetGatewayId=igw['InternetGateway']['InternetGatewayId'], VpcId=vpc_id)
        print(f"Created IGW: {igw['InternetGateway']['InternetGatewayId']}")
    else:
        print(f"Using existing IGW: {igw['InternetGatewayId']}")

    rt = get_resource_by_name('route-table', RT_NAME)
    if not rt:
        rt = ec2.create_route_table(VpcId=vpc_id)
        ec2.create_tags(Resources=[rt['RouteTable']['RouteTableId']], Tags=[{'Key': 'Name', 'Value': RT_NAME}])
        ec2.create_route(RouteTableId=rt['RouteTable']['RouteTableId'], DestinationCidrBlock='0.0.0.0/0', GatewayId=igw['InternetGateway']['InternetGatewayId'])
        ec2.associate_route_table(RouteTableId=rt['RouteTable']['RouteTableId'], SubnetId=subnet1['Subnet']['SubnetId'])
        ec2.associate_route_table(RouteTableId=rt['RouteTable']['RouteTableId'], SubnetId=subnet2['Subnet']['SubnetId'])
        print(f"Created Route Table: {rt['RouteTable']['RouteTableId']}")
    else:
        print(f"Using existing Route Table: {rt['RouteTableId']}")

    return vpc_id, subnet1['Subnet']['SubnetId'], subnet2['Subnet']['SubnetId']


# -------- Security Group --------
def create_security_group(vpc_id):
    sg = get_resource_by_name('sg', SG_NAME)
    if not sg:
        sg = ec2.create_security_group(GroupName=SG_NAME, Description='Allow required traffic', VpcId=vpc_id)
        sg_id = sg['GroupId']
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 6443, 'ToPort': 6443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 3000, 'ToPort': 3000, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 3001, 'ToPort': 3001, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 3002, 'ToPort': 3002, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        print(f"Created Security Group: {sg_id}")
    else:
        sg_id = sg['GroupId']
        print(f"Using existing Security Group: {sg_id}")
    return sg_id


# -------- User Data --------
def get_backend_user_data():
    return f'''#!/bin/bash
set -e
apt-get update -y && apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg unzip lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker && systemctl start docker
usermod -aG docker ubuntu
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com
docker pull {BACKEND_HELLO_IMG}
docker run -d --restart always -p 3001:3001 -e PORT=3001 -e MONGO_URL="{MONGO_URL}" {BACKEND_HELLO_IMG}
docker pull {BACKEND_PROFILE_IMG}
docker run -d --restart always -p 3002:3002 -e PORT=3002 -e MONGO_URL="{MONGO_URL}" {BACKEND_PROFILE_IMG}
'''


def get_frontend_user_data(alb_dns_hello, alb_dns_profile):
    return f'''#!/bin/bash
set -e
apt-get update -y && apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg unzip lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker && systemctl start docker
usermod -aG docker ubuntu
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com
docker pull {FRONTEND_IMG}
docker run -d -p 3000:3000 \
  -e REACT_APP_HELLO_API="http://{alb_dns_hello}" \
  -e REACT_APP_PROFILE_API="http://{alb_dns_profile}" \
  {FRONTEND_IMG}
'''


# -------- Launch Template --------
def create_launch_template(name, sg_id):
    lt = get_resource_by_name('launch-template', name)
    if not lt:
        lt = ec2.create_launch_template(
            LaunchTemplateName=name,
            LaunchTemplateData={
                'ImageId': AMI_ID,
                'InstanceType': INSTANCE_TYPE,
                'KeyName': KEY_NAME,
                'SecurityGroupIds': [sg_id],
                'IamInstanceProfile': {'Name': IAM_INSTANCE_PROFILE},
                'UserData': base64.b64encode(get_backend_user_data().encode()).decode()
            }
        )
        print(f"Created Launch Template: {lt['LaunchTemplate']['LaunchTemplateId']}")
    else:
        print(f"Using existing Launch Template: {lt['LaunchTemplateId']}")


# -------- ALBs --------
def create_hello_alb(subnet_ids, sg_id, vpc_id):
    alb = get_resource_by_name('alb', ALB_HELLO_NAME)
    if not alb:
        alb = elbv2.create_load_balancer(
            Name=ALB_HELLO_NAME,
            Subnets=subnet_ids,
            SecurityGroups=[sg_id],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )
        alb_dns = alb['LoadBalancers'][0]['DNSName']
        tg = elbv2.create_target_group(
            Name=TG_HELLO_NAME,
            Protocol='HTTP',
            Port=3001,
            VpcId=vpc_id,
            TargetType='instance'
        )
        tg_arn = tg['TargetGroups'][0]['TargetGroupArn']
        elbv2.create_listener(
            LoadBalancerArn=alb['LoadBalancers'][0]['LoadBalancerArn'],
            Protocol='HTTP',
            Port=80,
            DefaultActions=[{'Type': 'forward', 'TargetGroupArn': tg_arn}]
        )
        print(f"Created Hello ALB: {alb_dns}")
    else:
        alb_dns = alb['DNSName']
        tg = get_resource_by_name('target-group', TG_HELLO_NAME)
        tg_arn = tg['TargetGroupArn']
        print(f"Using existing Hello ALB: {alb_dns}")
    return alb_dns, tg_arn


def create_profile_alb(subnet_ids, sg_id, vpc_id):
    alb = get_resource_by_name('alb', ALB_PROFILE_NAME)
    if not alb:
        alb = elbv2.create_load_balancer(
            Name=ALB_PROFILE_NAME,
            Subnets=subnet_ids,
            SecurityGroups=[sg_id],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )
        alb_dns = alb['LoadBalancers'][0]['DNSName']
        tg = elbv2.create_target_group(
            Name=TG_PROFILE_NAME,
            Protocol='HTTP',
            Port=3002,
            VpcId=vpc_id,
            TargetType='instance'
        )
        tg_arn = tg['TargetGroups'][0]['TargetGroupArn']
        elbv2.create_listener(
            LoadBalancerArn=alb['LoadBalancers'][0]['LoadBalancerArn'],
            Protocol='HTTP',
            Port=80,
            DefaultActions=[{'Type': 'forward', 'TargetGroupArn': tg_arn}]
        )
        print(f"Created Profile ALB: {alb_dns}")
    else:
        alb_dns = alb['DNSName']
        tg = get_resource_by_name('target-group', TG_PROFILE_NAME)
        tg_arn = tg['TargetGroupArn']
        print(f"Using existing Profile ALB: {alb_dns}")
    return alb_dns, tg_arn


# -------- ASG --------
def create_asg(name, lt_name, subnet_ids, tg_arns):
    asg = get_resource_by_name('asg', name)
    if not asg:
        autoscaling.create_auto_scaling_group(
            AutoScalingGroupName=name,
            LaunchTemplate={'LaunchTemplateName': lt_name},
            MinSize=1,
            MaxSize=3,
            DesiredCapacity=1,
            VPCZoneIdentifier=','.join(subnet_ids),
            TargetGroupARNs=tg_arns
        )
        print(f"Created ASG: {name}")
    else:
        print(f"Using existing ASG: {name}")


# -------- Frontend EC2 --------
def create_frontend_ec2(subnet_id, sg_id, alb_dns_hello, alb_dns_profile):
    instances = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [FRONTEND_NAME]}])
    if not instances['Reservations']:
        instance = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_NAME,
            SecurityGroupIds=[sg_id],
            IamInstanceProfile={'Name': IAM_INSTANCE_PROFILE},
            SubnetId=subnet_id,
            MinCount=1,
            MaxCount=1,
            UserData=get_frontend_user_data(alb_dns_hello, alb_dns_profile),
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': FRONTEND_NAME}]
            }]
        )
        instance_id = instance['Instances'][0]['InstanceId']
        print(f"Created Frontend EC2: {instance_id}")
    else:
        print(f"Using existing Frontend EC2")


# -------- Main --------
def main():
    vpc_id, subnet1_id, subnet2_id = create_vpc_and_network()
    sg_id = create_security_group(vpc_id)
    create_launch_template(LT_BACKEND_NAME, sg_id)
    alb_dns_hello, tg_hello_arn = create_hello_alb([subnet1_id, subnet2_id], sg_id, vpc_id)
    alb_dns_profile, tg_profile_arn = create_profile_alb([subnet1_id, subnet2_id], sg_id, vpc_id)
    create_asg(ASG_BACKEND_NAME, LT_BACKEND_NAME, [subnet1_id, subnet2_id], [tg_hello_arn, tg_profile_arn])
    create_frontend_ec2(subnet1_id, sg_id, alb_dns_hello, alb_dns_profile)
    print(f"Hello ALB: {alb_dns_hello}")
    print(f"Profile ALB: {alb_dns_profile}")


if __name__ == "__main__":
    main()
