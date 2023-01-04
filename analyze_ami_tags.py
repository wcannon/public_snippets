#!/usr/bin/env python3
import boto3
import sys
import pprint
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

'''Objective: create an easy way to gather info for all ASG launch templates, and update them as well'''


def main():
  ec2 = boto3.resource('ec2') # can call this with a specific region e.g. boto3.resource('ec2', region_name='us-west-2')
  client = boto3.client('ec2')
  response = client.describe_images(Owners=['self'])
  images =  response['Images']
  amis = []

def describe_group(group_name):
    """
    Gets information about an Auto Scaling group.
    :param group_name: The name of the group to look up.
    :return: Information about the group, if found.
    """
    try:
        response = boto3.autoscaling_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[group_name])
    except ClientError as err:
        logger.error(
            "Couldn't describe group %s. Here's why: %s: %s", group_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        groups = response.get('AutoScalingGroups', [])
        return groups[0] if len(groups) > 0 else None


if __name__ == "__main__":
  print("Hello, world!")
  #main()
