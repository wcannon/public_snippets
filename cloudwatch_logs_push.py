#!/usr/bin/env python3 
import boto3
import time
from datetime import datetime
import pprint

AWS_REGION = "us-west-2"
client = boto3.client('logs', region_name=AWS_REGION)
messages = ["Request Processed Successfully", "Request Failed",
            "Unknown Response", "Email Sent"]

seq_token = None

response = client.put_log_events(
    logGroupName = 'bigid',
    logStreamName = 'ApplicationLogs',
    logEvents=[
        {
            'timestamp': int(time.time() * 1000),
            'message': f'nothing to see here, kidding - just this line {time.time()}'
        }
    ]
)

print("Logs generated successfully")
print("RESPONSE")
pprint.pprint(response)