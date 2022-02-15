##
## This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved. 
## Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
##
## The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
##
import json
import uuid
import boto3
import os
from module.utils import append_cors_headers, append_secure_headers, require_env
import datetime
import base64

ttl_sec = os.environ.get("TTL_SEC", (60 * 60 * 24) * 20) # 20 days

JOBS_TABLE_NAME = require_env('JOBS_TABLE_NAME')
JOBS_SQS_NAME = require_env('JOBS_SQS_NAME')
aws_region = os.environ.get("AWS_REGION", "us-east-1")
sqs = boto3.client("sqs", region_name=aws_region)
queueUrl = sqs.get_queue_url(QueueName=JOBS_SQS_NAME)['QueueUrl']

dynamodb = boto3.resource('dynamodb') # todo , endpoint_url="http://localhost:8000") for localstack
job_table = dynamodb.Table(JOBS_TABLE_NAME)

def handler(event, context):
    print(json.dumps(event))
    # todo validate request in api gateway
    if "body" not in event:
        raise Exception("bad request")

    train_request = json.loads(base64.b64decode(event["body"]))
    if "mentor" not in train_request:
        raise Exception("bad request")
    mentor = train_request["mentor"]

    # reject if there's already a train job for this mentor?

    job_id  = str(uuid.uuid4())
    train_job = {
        "id": job_id,
        "mentor": mentor,
        "status": 'QUEUED',
        "created": datetime.datetime.now().isoformat(),
        # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-before-you-start.html#time-to-live-ttl-before-you-start-formatting
        "ttl": int(datetime.datetime.now().timestamp()) + ttl_sec
    }
    print(train_job)
    sqs_msg = sqs.send_message(QueueUrl= queueUrl, MessageBody=json.dumps(train_job))
    print(sqs_msg) # for debugging

    job_table.put_item(Item=train_job)

    body = {
        "data": {
            "id": job_id,
            "mentor": mentor,
            "status": 'QUEUED',
            "statusUrl":f"/train/status/{job_id}",
        }
    }
    headers = {}
    append_cors_headers(headers, event)
    append_secure_headers(headers)
    dynamo_msg = {
        "statusCode": 200, # or 201?
        "body": json.dumps(body),
        "headers": headers
    }

    return dynamo_msg


# # for local debugging:
# if __name__ == '__main__':
#     handler({}, {})
# if __name__ == '__main__':
#     with open('__events__/train-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
