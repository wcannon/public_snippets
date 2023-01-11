#!/usr/bin/env python3
import boto3
import sys
import pprint
import logging
from botocore.exceptions import ClientError
import argparse

logger = logging.getLogger(__name__)

REGIONS = ["us-west-2", "us-east-1"]

def get_asgs(client):
  '''Return a list of all ASGs for a region'''
  # 'describe_auto_scaling_groups',
  groups = client.describe_auto_scaling_groups()['AutoScalingGroups']
  return groups

def describe_group(client, group_name):
    """
    Gets information about an Auto Scaling group.
    :param group_name: The name of the group to look up.
    :return: Information about the group, if found.
    """
    try:
        response = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[group_name])
    except ClientError as err:
        logger.error(
            "Couldn't describe group %s. Here's why: %s: %s", group_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        groups = response.get('AutoScalingGroups', [])
        return groups[0] if len(groups) > 0 else None

def get_launch_template_version(asg):
    version = "Not using launch template"
    lt = asg.get('LaunchTemplate', None)
    if lt:
        version = lt.get('Version', None)
    return version

def main(dry_run=True, num_asg=None, asg_name=None, region=None):
    # Update one asg only - for testing purposes, assuming us-west-2 region
    if asg_name:  
        update_asg_tag(region, asg_name)
    # Update only up to the value of num_asg - for batch testing purposes
    elif num_asg:
        count = 0
        stop = 0
        for region in REGIONS:
            asg_client = boto3.client('autoscaling', region_name=region)
            asgs = get_asgs(asg_client)
            asg_count = len(asgs)
            if num_asg < asg_count: 
                stop = num_asg
            else: 
                stop = asg_count
            for asg in asgs:
                update_asg_tag(region, asg)
                count = count + 1
            if count >= stop:
                sys.exit(0) # Exit early b/c we are at the batch size limit
    else:
        for region in REGIONS:
            asg_client = boto3.client('autoscaling', region_name=region)
            asgs = get_asgs(asg_client)
            for asg in asgs:
                update_asg_tag(region, asg)


def update_asg_tag(region='us-west-2', asg_name=None):
    for region in REGIONS:
        print("-"*80)
        print("-"*80)
        ec2_client = boto3.client('ec2', region_name=region)
        asg_client = boto3.client('autoscaling', region_name=region)
        asgs = get_asgs(asg_client)
        print(f"Launch Template Version: {get_launch_template_version(asg)}")
        print("*" * 80)

if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-n", "--num_asg", help="Number of ASGs to update", default=None, type=int)
    argParser.add_argument("-d", "--dry_run", help="Dry run mode", default=True)
    argParser.add_argument("-a", "--asg_name", help="Update Specific ASG by Name", default=None)
    argParser.add_argument("-r", "--region", help="Region name for ASG", default=None)

    args = argParser.parse_args()
    dry_run = bool(args.dry_run)  # passed in value is actually taken as string, must cast to bool
    
    print("args=%s" % args)
    print("*"*80)
    print("args.num_asg=%s" % args.num_asg)
    print("args.dry_run=%s" % args.dry_run)
    print("args.asg_name=%s" % args.asg_name)
    print("args.region=%s" % args.region)

    #main(dry_run, args.num_asg, args.asg_name, args.region)

'''
In a region, gather all asgs
- determine if it has a launch template
    no? -> capture region, name to a file for later and skip to next asg
- determine launch template name
- determine launch template version
- get all launch template info using describe_launch_template_versions, passing in version from asg
- determine if Vendor_Managed_AMI tag exists
    yes? -> skip to next asg
    no? -> determine value for tag (true|false), and create new launch template version with new tag and value
- if asg lt version to use is:
    $Default -> update launch template definition of Default to be our new version
    an integer -> update ASG definition to use our version int(version)
    $Latest -> noop 

** Should also support:
- dry run - just show what would be done
- limit to number of ASGs to act on (e.g. only run against X ASGs, then exit)



'''