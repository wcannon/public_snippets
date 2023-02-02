#!/usr/bin/env python3
import boto3
import pprint
import datetime

AWS_REGION = "us-west-2"

def get_log_stream_names(client, logGroupName):
    # return a list of log stream names from one log group
    stream_names = []
    try:
        response = client.describe_log_streams(
            logGroupName=logGroupName,
            orderBy='LogStreamName',
            descending=True,
        )
    except Exception as e:
        raise(e)

    log_stream_list = response['logStreams']
    for stream in log_stream_list:
        name = stream.get('logStreamName', 'Error')
        stream_names.append(name)
    return stream_names

def get_todays_stream_name():
    # create a string representing today e.g.  2023-02-03
    today = datetime.datetime.now()
    today_str = f"{today.strftime('%Y-%m-%d')}"
    return today_str

def create_log_stream(client, logGroupName, logStreamName):
    # create a log stream for a specific log group
    try:
        response = client.create_log_stream(
            logGroupName=logGroupName,
            logStreamName=logStreamName
        )
    except Exception as e:
        raise(e)
    return response

if __name__ == "__main__":
    client = boto3.client('logs', region_name=AWS_REGION)
    stream_names = get_log_stream_names(client, 'bigid')

    today += "-repeat"
    if today in stream_names:
        print("found it, don't need to create it")
    else:
        print("not found, creating it")
        create_log_stream(client, 'bigid', today)