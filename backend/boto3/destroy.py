import boto3
import time
import json
from botocore.exceptions import ClientError


region = "ap-south-1"
TAG_PREFIX = "ankit-anand-monday"

ec2 = boto3.client("ec2", region_name=region)
elbv2 = boto3.client("elbv2", region_name=region)
autoscaling = boto3.client("autoscaling", region_name=region)
iam = boto3.client("iam", region_name=region)
ec2_resource = boto3.resource("ec2", region_name=region)

# -------------------------------
# 1. Delete Auto Scaling Group
# -------------------------------
print("Deleting Auto Scaling Group...")
try:
    autoscaling.update_auto_scaling_group(
        AutoScalingGroupName=f"{TAG_PREFIX}-asg", MinSize=0, MaxSize=0, DesiredCapacity=0
    )
    autoscaling.delete_auto_scaling_group(
        AutoScalingGroupName=f"{TAG_PREFIX}-asg", ForceDelete=True
    )
except ClientError as e:
    print(f"[!] ASG Error: {e}")

# -------------------------------
# 2. Delete Launch Template
# -------------------------------
print("Deleting Launch Template...")
try:
    ec2.delete_launch_template(LaunchTemplateName=f"{TAG_PREFIX}-lt")
except ClientError as e:
    print(f"[!] Launch Template Error: {e}")

# -------------------------------
# 3. Terminate EC2 Instances
# -------------------------------
print("Terminating EC2 instances...")
instances = ec2.describe_instances(Filters=[
    {"Name": "tag:Name", "Values": [f"{TAG_PREFIX}-frontend", f"{TAG_PREFIX}-backend"]}
])
for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        instance_id = instance["InstanceId"]
        print(f"Terminating instance: {instance_id}")
        ec2.terminate_instances(InstanceIds=[instance_id])
        ec2.get_waiter("instance_terminated").wait(InstanceIds=[instance_id])

# -------------------------------
# 4. Delete Load Balancer & Target Group
# -------------------------------
print("Deleting Load Balancer and Target Group...")
try:
    lbs = elbv2.describe_load_balancers(Names=[f"{TAG_PREFIX}-alb"])
    lb_arn = lbs["LoadBalancers"][0]["LoadBalancerArn"]

    listeners = elbv2.describe_listeners(LoadBalancerArn=lb_arn)
    for listener in listeners["Listeners"]:
        elbv2.delete_listener(ListenerArn=listener["ListenerArn"])

    elbv2.delete_load_balancer(LoadBalancerArn=lb_arn)
    print("Waiting for Load Balancer to delete...")
    time.sleep(20)  # wait before deleting TG

    tgs = elbv2.describe_target_groups(Names=[f"{TAG_PREFIX}-tg"])
    tg_arn = tgs["TargetGroups"][0]["TargetGroupArn"]
    elbv2.delete_target_group(TargetGroupArn=tg_arn)

except ClientError as e:
    print(f"[!] ELB Error: {e}")

# -------------------------------
# 5. Delete Security Group
# -------------------------------
print("Deleting Security Group...")
try:
    sgs = ec2.describe_security_groups(Filters=[
        {"Name": "group-name", "Values": [f"{TAG_PREFIX}-sg"]}
    ])
    for sg in sgs["SecurityGroups"]:
        ec2.delete_security_group(GroupId=sg["GroupId"])
except ClientError as e:
    print(f"[!] Security Group Error: {e}")

# -------------------------------
# 6. Detach and Delete Internet Gateway
# -------------------------------
print("Detaching and deleting IGW...")
try:
    igws = ec2.describe_internet_gateways()
    for igw in igws["InternetGateways"]:
        for tag in igw.get("Tags", []):
            if tag["Key"] == "Name" and tag["Value"].startswith(TAG_PREFIX):
                igw_id = igw["InternetGatewayId"]
                for attachment in igw.get("Attachments", []):
                    try:
                        ec2.detach_internet_gateway(
                            InternetGatewayId=igw_id,
                            VpcId=attachment["VpcId"]
                        )
                    except ClientError:
                        pass
                ec2.delete_internet_gateway(InternetGatewayId=igw_id)
except ClientError as e:
    print(f"[!] IGW Error: {e}")

# -------------------------------
# 7. Delete Subnets
# -------------------------------
print("Deleting Subnets...")
try:
    subnets = ec2.describe_subnets()
    for subnet in subnets["Subnets"]:
        for tag in subnet.get("Tags", []):
            if tag["Key"] == "Name" and tag["Value"].startswith(TAG_PREFIX):
                ec2.delete_subnet(SubnetId=subnet["SubnetId"])
except ClientError as e:
    print(f"[!] Subnet Error: {e}")

# -------------------------------
# 8. Delete Route Tables
# -------------------------------
print("Deleting Route Tables...")
try:
    rtables = ec2.describe_route_tables()
    for rt in rtables["RouteTables"]:
        for tag in rt.get("Tags", []):
            if tag["Key"] == "Name" and tag["Value"].startswith(TAG_PREFIX):
                associations = rt.get("Associations", [])
                for assoc in associations:
                    if not assoc.get("Main", False):
                        try:
                            ec2.disassociate_route_table(AssociationId=assoc["RouteTableAssociationId"])
                        except ClientError:
                            pass
                try:
                    ec2.delete_route_table(RouteTableId=rt["RouteTableId"])
                except ClientError:
                    pass
except ClientError as e:
    print(f"[!] Route Table Error: {e}")

# -------------------------------
# 9. Delete VPC
# -------------------------------
print("Deleting VPC...")
try:
    vpcs = ec2.describe_vpcs()
    for vpc in vpcs["Vpcs"]:
        for tag in vpc.get("Tags", []):
            if tag["Key"] == "Name" and tag["Value"] == f"{TAG_PREFIX}-vpc":
                ec2.delete_vpc(VpcId=vpc["VpcId"])
except ClientError as e:
    print(f"[!] VPC Error: {e}")

# -------------------------------
# 10. Delete IAM Role and Instance Profile
# -------------------------------
print("Deleting IAM Role and Instance Profile...")
try:
    role_name = f"{TAG_PREFIX}-ec2-role"
    iam.remove_role_from_instance_profile(InstanceProfileName=role_name, RoleName=role_name)
    iam.delete_instance_profile(InstanceProfileName=role_name)
    iam.detach_role_policy(RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly")
    iam.delete_role(RoleName=role_name)
except ClientError as e:
    print(f"[!] IAM Error: {e}")

print("\n✅ All tagged resources with prefix", TAG_PREFIX, "have been deleted.")
