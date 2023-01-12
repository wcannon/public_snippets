#!/usr/bin/env python3
import boto3
import sys
import pprint
import logging
from botocore.exceptions import ClientError
import argparse
import datetime

logger = logging.getLogger(__name__)

REGIONS = ["us-west-2"]
FILENAME = "asgs_using_launch_config.txt"

def write_launch_config_asg_file(region, asg_name):
    f = open(FILENAME, 'w+')
    f.write(f"region: {region}, asg_name: {asg_name}")
    f.close()
    return

def get_asgs(client, asg_name=None):
    '''Return a list of either one, or all ASGs for a region'''
    if asg_name:
        groups = client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])['AutoScalingGroups']
        if len(groups) == 0:
            print("ASG not found, exiting")
            sys.exit(1)
    else:
        groups = client.describe_auto_scaling_groups()['AutoScalingGroups']
    return groups

def get_launch_template_version(asg):
    version = "Not using launch template"
    lt = asg.get('LaunchTemplate', None)
    if lt:
        version = lt.get('Version', None)
    return version

def get_lt_info(ec2_client, template_name, version):
  response = ec2_client.describe_launch_template_versions(
    LaunchTemplateName=template_name,
    Versions=[
        version,
    ]
  )
  return response

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
        instance_tags_list = tag_type.get('Tags')
        for dict in instance_tags_list:
          print(f"tag_dict: {dict}")
          if dict['Key'] == 'Vendor_Managed_AMI':
            return True
  return result

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

def create_new_launch_template(ec2_client, lt_name, lt_version, lt_dict):
  '''Create a new launch template, simply updating it with our new tag dictionary'''
  response = ec2_client.create_launch_template_version(LaunchTemplateName=lt_name,
                                            SourceVersion=lt_version,
                                            LaunchTemplateData=lt_dict)
  return response

def update_asg_launch_template_version(asg_client, asg_name, template_name, template_version):
    '''Update the asg to use a new template version'''
    # e.g. asg set to use specific version, we modify it to use our new version number
    response = asg_client.update_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchTemplate={
            'LaunchTemplateName': template_name,
            'Version': template_version
     })
    return response

def update_launch_template_default(ec2_client, template_name, new_lt_version):
    version_update_response = ec2_client.modify_launch_template(
        DryRun=False,
        #ClientToken='string',
        #LaunchTemplateId='string',
        LaunchTemplateName=template_name,
        DefaultVersion=str(new_lt_version)
        )
    return version_update_response

def main(dry_run=True, num_asg=None, asg_name=None, region=None):
    ec2_client = boto3.client('ec2', region_name=region)
    asg_client = boto3.client('autoscaling', region_name=region)
    asgs = get_asgs(asg_client)
    asg_count = len(asgs)

    # Update one asg only - for testing purposes, assuming us-west-2 region
    if asg_name:  
        # get an asg, pass it to update_asg_tag fn
        ec2_client = boto3.client('ec2', region_name=region)
        asg_client = boto3.client('autoscaling', region_name=region)
        asg_list = get_asgs(asg_client, asg_name) # should have 1 element
        update_asg_tag(ec2_client, asg_client, region, asg_list[0])
    # Update only up to the value of num_asg - for batch testing purposes e.g. update 5 and review data
    elif num_asg:
        count = 0
        stop = 0
        for reg in REGIONS:
            ec2_client = boto3.client('ec2', region_name=reg)
            asg_client = boto3.client('autoscaling', region_name=reg)
            asgs = get_asgs(asg_client)
            asg_count = len(asgs)
            if num_asg < asg_count: 
                stop = num_asg
            else: 
                stop = asg_count
            for asg in asgs:
                update_asg_tag(ec2_client, asg_client, region, asg)
                count = count + 1
                if count >= stop:
                    print(f"Count: {count}")
                    sys.exit(0) # Exit early b/c we are at the batch size limit
    # Update all the ASGs in all regions
    else:
        for reg in REGIONS:
            ec2_client = boto3.client('ec2', region_name=reg)
            asg_client = boto3.client('autoscaling', region_name=reg)
            asgs = get_asgs(asg_client)    
            for asg in asgs:
                update_asg_tag(ec2_client, asg_client, region, asg)


def update_asg_tag(ec2_client=None, asg_client=None, region=None, asg=None):
    '''Update an asg launch template tag for Vendor_Managed_AMI'''
    print("-"*80)
    print("-"*80)
    pprint.pprint(asg)
    asg_name = asg['AutoScalingGroupName']

    if 'LaunchConfigurationName' in asg.keys():
        try:
            region = asg['AvailabilityZones'][0][:-1]
        except Exception as e:
            region = "unknown"
            pass

        write_launch_config_asg_file(region, asg_name)
        return
    
    # ASG using launch template, gathering info
    template_name = asg['LaunchTemplate']['LaunchTemplateName']
    template_version = asg['LaunchTemplate']['Version']
    print("-"*80)
    print(f"asg template_version to use: {template_version}")
    print("-"*80)
    lt_info = get_lt_info(ec2_client, template_name, template_version)
    image_id = lt_info['LaunchTemplateVersions'][0]['LaunchTemplateData']['ImageId']
    lt_version = str(lt_info['LaunchTemplateVersions'][0]['VersionNumber'])
    print("-"*80)
    print(f"lt_version: {lt_version}")
    print("-"*80)
    print("Launch Template Info")
    pprint.pprint(lt_info)
    print("-"*80)
    print(f"ImageID: {image_id}")
    print("-"*80)
    vma_exists = determine_if_VMA_tag_exists(lt_info)
    print(f"VMA tag exists: {vma_exists}")
    if vma_exists: # don't need to add a tag
        print(f"Vendor_Managed_AMI tag exists for launch template: {template_name}")
        return

    print("-"*80)
    image_location, ami_name, owner_id = get_ami_info(ec2_client, image_id)
    print(f"image_location: {image_location}\n ami_name: {ami_name}\n owner_id: {owner_id}\n")
    print("-" * 80)
    vma_tag_value = get_vendor_tag_value(image_location, ami_name, owner_id) # will be true or false or tbd
    print(f"vma_tag_value: {vma_tag_value}")
    print("-" * 80)
    TagSpecifications = create_instance_tags_list(lt_info, vma_tag_value)   
    lt_dict = {'TagSpecifications': TagSpecifications}
    new_lt = create_new_launch_template(ec2_client, template_name, lt_version, lt_dict)
    new_lt_version = new_lt['LaunchTemplateVersion']['VersionNumber']
    print("*" * 80)
    print(f"New launch template version: {new_lt_version}")
    print("-"*80)
    if template_version.isdigit(): # have to update the asg to use new version number
        print("Updating ASG to use our new version number")
        print(asg_client, asg_name, template_name, new_lt_version)
        r1 = update_asg_launch_template_version(asg_client, asg_name, template_name, str(new_lt_version))
        #pprint.pprint(r1)
    elif template_version == "$Default": # have to update launch template value of $Default
        print("Updating $Default to have our latest version number")
        update_launch_template_default(ec2_client, template_name, str(new_lt_version))
    elif template_version == "$Latest": # no work to do, will use our newer version
        print("ASG set to use latest, continuing")
    else:
        print("Should not see this printed - new corner case found")
    return



if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-n", "--num_asg", help="Number of ASGs to update", default=None, type=int)
    argParser.add_argument("-d", "--dry_run", help="Dry run mode", default=True)
    argParser.add_argument("-a", "--asg_name", help="Update Specific ASG by Name, requires -r region flag also", default=None)
    argParser.add_argument("-r", "--region", help="Region name for ASG", default=None)

    args = argParser.parse_args()
    dry_run = bool(args.dry_run)  # passed in value is actually taken as string, must cast to bool
    
    '''print("args=%s" % args)
    print()
    print("*"*80)
    print("args.num_asg=%s" % args.num_asg)
    print("args.dry_run=%s" % args.dry_run)
    print("args.asg_name=%s" % args.asg_name)
    print("args.region=%s" % args.region)
    print("*"*80)
    print()
    '''
    main(dry_run, args.num_asg, args.asg_name, args.region)

'''
In a region, gather all asgs
- DONE determine if it has a launch template
    no? -> capture region, name to a file for later and skip to next asg
- DONE determine launch template name
- DONE determine launch template version
- DONE get all launch template info using describe_launch_template_versions, passing in version from asg
- determine if Vendor_Managed_AMI tag exists
    yes? -> skip to next asg
    no? -> determine value for tag (true|false), and create new launch template version with new tag and value
    ** update get_vendor_tag_value() with actual logic
- if asg lt version to use is:
    $Default -> update launch template definition of Default to be our new version
    an integer -> update ASG definition to use our version int(version)
    $Latest -> noop 

** Should also support:
- dry run - just show what would be done
- DONE limit to number of ASGs to act on (e.g. only run against X ASGs, then exit)



'''