#!/usr/bin/env python3
import boto3
import sys
import pprint
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

REGIONS = ["us-east-1", "us-west-2"]

'''Objective: create an easy way to gather info for all ASG launch templates, and update them as well'''

def get_asgs(client):
  '''Return a list of all ASGs for a region'''
  # 'describe_auto_scaling_groups',
  groups = client.describe_auto_scaling_groups()['AutoScalingGroups']
  print("*"*80)
  print(f"Number of ASGs found: {len(groups)}")
  for g in groups:
    print(f"Name: {g['AutoScalingGroupName']}")
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

def get_lt_template(ec2_client, template_name):
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

def get_lt_info(ec2_client, template_name):
  response = ec2_client.describe_launch_template_versions(
    LaunchTemplateName=template_name,
    Versions=[
        '$Default',
    ]
  )
  return response

def get_ami_id(response):
  '''Return just hte ImageID for the AMI'''
  return response['LaunchTemplateVersions'][0]['LaunchTemplateData']['ImageId']

def get_ami_info(ec2_client, ami_id):
  '''Looks up and returns ami_name, owner, location'''
  image_info = ec2_client.describe_images(ImageIds=[ami_id])
  image_location = "none"
  ami_name = "none"
  owner_id = "none"
  if len(image_info['Images']) > 0:
    image = image_info['Images'][0]
    image_location = image['ImageLocation']
    ami_name = image['Name']
    owner_id = image['OwnerId']
  return image_location, ami_name, owner_id

def get_vendor_tag_value(image_location, ami_name, owner_id):
  '''fill out with logic later on - returns true, false, tbd'''
  return True

def update_launch_template(template_name, tag_value):
  '''Creates new version of launch template, returns version number, sets as default template to use'''
  # modify_launch_template()
  pass

def main():
  for region in REGIONS:
    print("-"*80)
    print("-"*80)
    print(f"NOW IN REGION: {region}")
    ec2_client = boto3.client('ec2', region_name=region)
    asg_client = boto3.client('autoscaling', region_name=region)
    asgs = get_asgs(asg_client)
    pprint.pprint(asgs)  
    for asg in asgs:
      lt = get_lt_template(ec2_client, asg['LaunchTemplate']['LaunchTemplateName'])
      print("-"*80)
      pprint.pprint(lt)
      response = get_lt_info(ec2_client, asg['LaunchTemplate']['LaunchTemplateName'])
      print("*" * 80)
      print("LAUNCH TEMPLATE INFO")
      pprint.pprint(f"{response}")
      ami_id = get_ami_id(response)
      print("*" * 80)
      print(f"AMI ImageID: {ami_id}") 
      image_location, ami_name, owner_id = get_ami_info(ec2_client, ami_id)
      print("*" * 80)
      print(f"image_location: {image_location}")
      print(f"ami_name: {ami_name}")
      print(f"owner_id: {owner_id}")
      tag_value = get_vendor_tag_value(image_location, ami_name, owner_id)


if __name__ == "__main__":
  main()


'''
TODO:
* Assuming we have a list of ASGs to act on (0+)
- get the default launch template id, name, version, tags, ami, 
- get ami details querying the data for the particular ami e.g. path 
- determine how to update the tags with new Vendor_Managed_AMI 
- create new launch template version from the current one, updating with our new tags 
- update launch template DefaultVersionNumber (using modify_launch_template() to use our new version number

Notes:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client
Can use create_launch_template_version(**kwargs)¶ to create a new launch template from a previous one, and update the tags
'''