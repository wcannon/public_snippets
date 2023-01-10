#!/usr/bin/env python3
import boto3
import sys
import pprint
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

#REGIONS = ["us-west-2", "us-east-1"]
REGIONS = ["us-west-2"]

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

def get_lt_name(response):
  '''Return the template name'''
  return response['LaunchTemplateVersions'][0]['LaunchTemplateData']['ImageId']

def get_launch_template_version(response):
  '''Return just hte ImageID for the AMI'''
  return response['LaunchTemplateVersions'][0]['VersionNumber']

def determine_if_VMA_tag_exists(response):
  '''Return True/False'''
  result = False
  lt_template_data = response['LaunchTemplateVersions'][0]['LaunchTemplateData']
  # Handle the case of no tags set at all
  if 'TagSpecifications' not in lt_template_data.keys():
    print("TagSpeicifcations not found in LaunchTemplateData")
    return False
  else:
    # Handle the case tag is missing
    tags_by_type = lt_template_data.get('TagSpecifications', None)
    for tag_type in tags_by_type:
      if tag_type.get('ResourceType') == "instance": # Found all the instance tags
        instance_tags = tag_type.get('Tags')
        for kv in instance_tags:
          if kv == 'Vendor_Managed_AMI':
            result = True
  return result

def create_instance_tags_list(response, VMA_value):
  '''Inspect a response, and return the correct TagSpecifications when adding our Vendor_Managed_AMI tag'''
  TagSpecifications = []
  lt_template_data = response['LaunchTemplateVersions'][0]['LaunchTemplateData']
  if 'TagSpecifications' not in lt_template_data.keys(): # no tags on any resource types at all
    TagSpecifications.append({'ResourceType': 'instance',
                               'Tags' : [ {'Key': 'Vendor_Managed_AMI', 'Value': VMA_value}]})
  else: # we preserve existing tags, and add ours to it
    tags_list = lt_template_data.get('TagSpecifications', None) # tags_list is a list of dicts
    for tags_dict in tags_list:
      if tags_dict.get('ResourceType') != "instance": # keep other types intact
        TagSpecifications.append(tags_dict)
      else: # we need to add our key/value and preserve the other instance tags
        new_tags_dict = {'ResourceType' : 'instance'}
        new_tags = tags_dict['Tags'][:] # get a copy, preserves all the current tags
        new_tags.append( {'Key':'Vendor_Managed_AMI', 'Value': VMA_value})
        new_tags_dict['Tags'] = new_tags
    TagSpecifications.append(new_tags_dict)
  return TagSpecifications 


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
  return "true"

def create_new_launch_template(ec2_client, lt_name, lt_version, lt_dict):
  '''Create a new launch template, simply updating it with our new tag dictionary'''
  response = ec2_client.create_launch_template_version(LaunchTemplateName=lt_name,
                                            SourceVersion=lt_version,
                                            LaunchTemplateData=lt_dict)
  return response

def update_launch_template(template_name, tag_value):
  '''Creates new version of launch template, returns version number, sets as default template to use'''
  # modify_launch_template()
  pass

def main(dry_run):
  for region in REGIONS:
    print("-"*80)
    print("-"*80)
    print(f"NOW IN REGION: {region}")
    ec2_client = boto3.client('ec2', region_name=region)
    asg_client = boto3.client('autoscaling', region_name=region)
    asgs = get_asgs(asg_client)
    pprint.pprint(asgs)  
    for asg in asgs:
      template_name = asg['LaunchTemplate']['LaunchTemplateName']
      lt = get_lt_template(ec2_client, template_name)
      print("-"*80)
      pprint.pprint(lt)
      response = get_lt_info(ec2_client, template_name)
      print("*" * 80)
      print("LAUNCH TEMPLATE INFO")
      pprint.pprint(response)
      print("*" * 80)
      # Check if tag for Vendor_Managed_AMI already exists, if so then skip this one
      VMA_tag_exists = determine_if_VMA_tag_exists(response)
      if VMA_tag_exists:
        print("VMA tag exists, SKIPPING this ASG")
        continue
      else:
        print("VMA tag does not exist, will CREATE this tag")
      print("*" * 80)
      ami_id = get_ami_id(response)
      lt_version = get_launch_template_version(response)
      print("*" * 80)
      print(f"AMI ImageID: {ami_id}") 
      print(f"launch template version: {lt_version}") 
      image_location, ami_name, owner_id = get_ami_info(ec2_client, ami_id)
      print("*" * 80)
      print(f"image_location: {image_location}")
      print(f"ami_name: {ami_name}")
      print(f"owner_id: {owner_id}")
      tag_value = get_vendor_tag_value(image_location, ami_name, owner_id)
      print("*" * 80)
      print(f"Vendor_Managed_AMI tag value will be: {tag_value}")
      print("*" * 80)     
      TagSpecifications = create_instance_tags_list(response, VMA_tag_exists)   
      if not dry_run: 
        new_lt = create_new_launch_template(ec2_client, template_name, str(lt_version), TagSpecifications)
        new_lt_version = new_lt['LaunchTemplateVersion']['VersionNumber']
        print("*" * 80)
        print(f"New launch template version: {new_lt_version}")
      else:
        print()
        print("*" * 80)
        print("*" * 80)
        print("Dry run enabled: skipping creation of new launch template, update of tags, switching asg to use new launch template")
        print("*" * 80)
        print("Current TagSpecifications are: ")
        pprint.pprint(TagSpecifications)


if __name__ == "__main__":
  dry_run = True
  if len(sys.argv) > 1:
    input = sys.argv[1]
    if "false" == input.lower():
      dry_run = False
  main(dry_run)


'''
TODO:
*** Should have a dry-run mode by default - just show what we found and what we would do if dry-run flag is set
* Assuming we have a list of ASGs to act on (0+)
- get the default launch template id, name, version, tags, ami, 
  - if Vendor_Managed_AMI already exists, skip to next ASG
- get ami details querying the data for the particular ami e.g. path 
- determine how to update the tags with new Vendor_Managed_AMI 
- create new launch template version from the template set as default, passing in our new tags 
  - MUST preserve the previous tags from the original launch template source as well, our new version will overwrite them all
- update launch template DefaultVersionNumber (using modify_launch_template() to use our new version number

Notes:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client
Can use create_launch_template_version(**kwargs)¶ to create a new launch template from a previous one, and update the tags


- get all the instance tags
- add my key/value to the list
- create new launch template version from the default template
- get the version number of the new template just created
- set that as the new default version to launch with
'''
