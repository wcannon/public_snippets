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

def get_template(ec2_client, template_name):
  """
  Gets a launch template. Launch templates specify configuration for instances
  that are launched by Amazon EC2 Auto Scaling.
  :param template_name: The name of the template to look up.
  :return: The template, if it exists.
  """
  try:
      response = ec2_client.describe_launch_templates(LaunchTemplateNames=[template_name])
      template = response['LaunchTemplates'][0]
  except ClientError as err:
      if err.response['Error']['Code'] == 'InvalidLaunchTemplateName.NotFoundException':
          logger.warning("Launch template %s does not exist.", template_name)
      else:
          logger.error(
              "Couldn't verify launch template %s. Here's why: %s: %s", template_name,
              err.response['Error']['Code'], err.response['Error']['Message'])
          raise
  else:
      return template

def do_it():
  ec2 = boto3.client('ec2')
  response = ec2.describe_instances()
  pprint.pprint(response)
  as_client = boto3.client('autoscaling')
  asg = describe_group(as_client, "test")
  print("-"*80)
  pprint.pprint(asg)
  print("-"*80)

  lt_name = asg['LaunchTemplate']['LaunchTemplateName']
  print(f"Launch Template Name: {lt_name}")
  print("-"*80)
  template = get_template(ec2, lt_name)
  pprint.pprint(template)
  print("-"*80)


def main2():
  do_it()
  

if __name__ == "__main__":
  print("Hello, world!")
  main2()
  #main()

'''
TODO:
1. in aws console, create asg
2. update code to get asg info
3. update code to get asg launch template
4. inspect tags
5. determine if Vendor_Managed_AMI tag is set correctly, or exists
6. correct it if need be and update launch template'''