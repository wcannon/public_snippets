#!/usr/bin/env python3
import boto3


TABLE_NAME = "audit_log"

def put_latest(table, value):
    table.put_item(
        Item = {'timestamp': 'latest', 'date_time': value}
    )

def get_latest(table):
    resp = table.get_item(
                Key = {'timestamp': 'latest'}
            )
    return resp

if __name__ == "__main__":
    # get a connection to dynamodb
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

    # push our data into the table
    table = dynamodb.Table('audit_log')
    put_latest(table, '12345679')

    response = get_latest(table)
    print(response['Item'])




