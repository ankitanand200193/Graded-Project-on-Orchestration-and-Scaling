import boto3
import time

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

# Boto3 clients
ec2 = boto3.client('ec2', region_name=region)
elbv2 = boto3.client('elbv2', region_name=region)
autoscaling = boto3.client('autoscaling', region_name=region)


# -------- Helper Functions --------
def get_resource_by_name(resource_type, name):
    try:
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
        elif resource_type == 'instance':
            reservations = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [name]}])['Reservations']
            if reservations:
                return [inst['InstanceId'] for res in reservations for inst in res['Instances']]
            return None
    except Exception:
        return None


# -------- Destroy Functions --------
def delete_asg(name):
    asg = get_resource_by_name('asg', name)
    if asg:
        print(f"Deleting ASG: {name}")
        autoscaling.update_auto_scaling_group(AutoScalingGroupName=name, MinSize=0, MaxSize=0, DesiredCapacity=0)
        time.sleep(20)
        autoscaling.delete_auto_scaling_group(AutoScalingGroupName=name, ForceDelete=True)
    else:
        print(f"No ASG found: {name}")


def delete_launch_template(name):
    lt = get_resource_by_name('launch-template', name)
    if lt:
        print(f"Deleting Launch Template: {name}")
        ec2.delete_launch_template(LaunchTemplateId=lt['LaunchTemplateId'])
    else:
        print(f"No Launch Template found: {name}")


def delete_alb_and_tg(alb_name, tg_name):
    alb = get_resource_by_name('alb', alb_name)
    if alb:
        alb_arn = alb['LoadBalancerArn']
        print(f"Deleting ALB: {alb_name}")

        # Delete listeners
        listeners = elbv2.describe_listeners(LoadBalancerArn=alb_arn)['Listeners']
        for listener in listeners:
            elbv2.delete_listener(ListenerArn=listener['ListenerArn'])

        elbv2.delete_load_balancer(LoadBalancerArn=alb_arn)
        time.sleep(15)
    else:
        print(f"No ALB found: {alb_name}")

    tg = get_resource_by_name('target-group', tg_name)
    if tg:
        print(f"Deleting Target Group: {tg_name}")
        elbv2.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])
    else:
        print(f"No Target Group found: {tg_name}")


def terminate_ec2(name):
    instances = get_resource_by_name('instance', name)
    if instances:
        print(f"Terminating EC2 instance(s): {instances}")
        ec2.terminate_instances(InstanceIds=instances)
        waiter = ec2.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instances)
    else:
        print(f"No EC2 instances found with name: {name}")


def delete_security_group(name):
    sg = get_resource_by_name('sg', name)
    if sg:
        print(f"Deleting Security Group: {name}")
        ec2.delete_security_group(GroupId=sg['GroupId'])
    else:
        print(f"No Security Group found: {name}")


def delete_route_table(name):
    rt = get_resource_by_name('route-table', name)
    if rt:
        print(f"Deleting Route Table: {name}")
        for assoc in rt.get('Associations', []):
            if not assoc['Main']:
                ec2.disassociate_route_table(AssociationId=assoc['RouteTableAssociationId'])
        ec2.delete_route_table(RouteTableId=rt['RouteTableId'])
    else:
        print(f"No Route Table found: {name}")


def delete_internet_gateway(name, vpc_id):
    igw = get_resource_by_name('igw', name)
    if igw:
        print(f"Deleting Internet Gateway: {name}")
        ec2.detach_internet_gateway(InternetGatewayId=igw['InternetGatewayId'], VpcId=vpc_id)
        ec2.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])
    else:
        print(f"No Internet Gateway found: {name}")


def delete_subnets(names):
    for n in names:
        subnet = get_resource_by_name('subnet', n)
        if subnet:
            print(f"Deleting Subnet: {n}")
            ec2.delete_subnet(SubnetId=subnet['SubnetId'])
        else:
            print(f"No Subnet found: {n}")


def delete_vpc(name):
    vpc = get_resource_by_name('vpc', name)
    if vpc:
        print(f"Deleting VPC: {name}")
        ec2.delete_vpc(VpcId=vpc['VpcId'])
    else:
        print(f"No VPC found: {name}")


# -------- Main Destroy Function --------
def main():
    print("Starting infrastructure teardown...")

    # 1. Terminate EC2
    terminate_ec2(FRONTEND_NAME)

    # 2. Delete ASG
    delete_asg(ASG_BACKEND_NAME)

    # 3. Delete ALBs and Target Groups
    delete_alb_and_tg(ALB_HELLO_NAME, TG_HELLO_NAME)
    delete_alb_and_tg(ALB_PROFILE_NAME, TG_PROFILE_NAME)

    # 4. Delete Launch Template
    delete_launch_template(LT_BACKEND_NAME)

    # 5. Delete Security Group
    delete_security_group(SG_NAME)

    # 6. Delete Route Table
    delete_route_table(RT_NAME)

    # 7. Delete Internet Gateway
    vpc = get_resource_by_name('vpc', VPC_NAME)
    vpc_id = vpc['VpcId'] if vpc else None
    if vpc_id:
        delete_internet_gateway(IGW_NAME, vpc_id)

    # 8. Delete Subnets
    delete_subnets([SUBNET1_NAME, SUBNET2_NAME])

    # 9. Delete VPC
    delete_vpc(VPC_NAME)

    print("Teardown complete.")


if __name__ == "__main__":
    main()
