#!/usr/bin/env python3
# # Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "token"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    print(f"session: {session}")
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        print(f"get_secret_value_response: {get_secret_value_response}")
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
        print(e)

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    print(f"Secret: {secret}")

get_secret()