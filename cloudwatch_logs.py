#!/usr/bin/env python

import sys
import os
import configparser
import time
import argparse

try:
    import boto3
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

if not HAS_BOTO:
    sys.stderr.write("Module boto3 required")
    sys.exit(1)


def send_logs_to_cloudwatch(group, stream, message):
    config = configparser.ConfigParser()
    ec2_cred_file = os.path.expanduser(os.path.expandvars("~/.aws/credentials"))
    ec2_conf_file = os.path.expanduser(os.path.expandvars("~/.aws/config"))

    if os.path.isfile(ec2_cred_file):
        config.read(ec2_cred_file)
        try:
            access_key = config.get("default", "aws_access_key_id")
        except:
            pass
        try:
            secret_key = config.get("default", "aws_secret_access_key")
        except:
            pass

    if os.path.isfile(ec2_conf_file):
        config.read(ec2_conf_file)
        try:
            region = config.get("default", "region")
        except:
            pass

    if 'AWS_ACCESS_KEY_ID' in os.environ:
        access_key = os.environ['AWS_ACCESS_KEY_ID']
    if 'AWS_SECRET_ACCESS_KEY' in os.environ:
        secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
    if 'AWS_DEFAULT_REGION' in os.environ:
        region = os.environ['AWS_DEFAULT_REGION']
    session = boto3.Session(aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            region_name=region)
    client = session.client('logs')

    try:
        client.create_log_group(logGroupName=group)
    except client.exceptions.ResourceAlreadyExistsException:
        pass

    try:
        client.create_log_stream(logGroupName=group, logStreamName=stream)
    except client.exceptions.ResourceAlreadyExistsException:
        pass

    log_events = dict(logGroupName=group,
                      logStreamName=stream,
                      logEvents=[{
                        'timestamp': int(time.time() * 1000),
                        'message': message
                      }])
    streams = client.describe_log_streams(logGroupName=group, logStreamNamePrefix=stream)
    for st in streams['logStreams']:
        if st['logStreamName'] == stream and 'uploadSequenceToken' in st:
            log_events['sequenceToken'] = st['uploadSequenceToken']
            break

    return client.put_log_events(**log_events)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("group", help="log group")
    parser.add_argument("stream", help="log stream")
    parser.add_argument("message", help="data to log")
    args = parser.parse_args()
    print(send_logs_to_cloudwatch(args.group, args.stream, args.message))
