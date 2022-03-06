#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
import json
import uuid
import boto3
import os
from module.utils import create_json_response, require_env, is_authorized, load_sentry
import datetime
import base64
from module.logger import get_logger


load_sentry()
log = get_logger("train")
ttl_sec = os.environ.get("TTL_SEC", (60 * 60 * 24) * 20)  # 20 days
JOBS_TABLE_NAME = require_env("JOBS_TABLE_NAME")
log.info(f"using table {JOBS_TABLE_NAME}")
JOBS_SQS_NAME = require_env("JOBS_SQS_NAME")
aws_region = os.environ.get("REGION", "us-east-1")
sqs = boto3.client("sqs", region_name=aws_region)
queue_url = sqs.get_queue_url(QueueName=JOBS_SQS_NAME)["QueueUrl"]
log.info(f"using queue {queue_url}")
# todo endpoint_url="http://localhost:8000") for localstack
dynamodb = boto3.resource("dynamodb", region_name=aws_region)
job_table = dynamodb.Table(JOBS_TABLE_NAME)


def handler(event, context):
    log.debug(json.dumps(event))
    if "body" not in event:
        raise Exception("bad request")

    if event["isBase64Encoded"]:
        body = base64.b64decode(event["body"])
    else:
        body = event["body"]
    train_request = json.loads(body)
    if "mentor" not in train_request:
        raise Exception("bad request")
    mentor = train_request["mentor"]
    token = json.loads(event["requestContext"]["authorizer"]["token"])

    if not is_authorized(mentor, token):
        data = {
            "error": "not authorized",
            "message": "not authorized",
        }
        return create_json_response(401, data, event)

    # reject if there's already a train job for this mentor?

    job_id = str(uuid.uuid4())
    train_job = {
        "id": job_id,
        "mentor": mentor,
        "status": "QUEUED",
        "created": datetime.datetime.now().isoformat(),
        # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-before-you-start.html#time-to-live-ttl-before-you-start-formatting
        "ttl": int(datetime.datetime.now().timestamp()) + ttl_sec,
    }
    log.debug(train_job)
    sqs_msg = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(train_job))
    log.info(sqs_msg)

    job_table.put_item(Item=train_job)

    data = {
        "id": job_id,
        "mentor": mentor,
        "status": "QUEUED",
        "statusUrl": f"/train/status/{job_id}",
    }
    return create_json_response(200, data, event)


# # for local debugging:
# if __name__ == '__main__':
#     with open('__events__/train-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
