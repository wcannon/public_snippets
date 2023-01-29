#!/usr/bin/env python3
import boto3


TABLE_NAME = "audit_log"
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('audit_log')
table.put_item(
    Item = {'timestamp': '2023-01-29'}
)


